// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;

import 'package:flutter/material.dart';

import '../data/accessibility_data.dart';
import '../utils/fetch.dart';
import 'widgets/section.dart';


class HomePage extends StatefulWidget {
  const HomePage({ super.key });

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final TextEditingController _urlController = TextEditingController();
  final PageController _pageController = PageController();
  List<AccessibilityData> _results = [];

  bool _isLoading = false;

  Future<void> _pickFile() async {
    html.FileUploadInputElement uploadInput = html.FileUploadInputElement();
    uploadInput.accept = '.csv, .txt';
    uploadInput.multiple = false;

    uploadInput.click();

    uploadInput.onChange.listen((e) async {
      final files = uploadInput.files;
      if (files!.isEmpty) {
        debugPrint('Файл не был выбран');
        return;
      }

      final file = files[0];
      final reader = html.FileReader();

      reader.onLoadEnd.listen((e) async {
        String fileContent = reader.result as String;

        String extension = file.name.split('.').last.toLowerCase();
        
        List<String> urls = _extractUrls(fileContent, extension);
        try {
          _results.clear();
          setState(() { _isLoading = true; });

          if (isValidUrl(_urlController.text)) {
            final data = await Fetch.fetchReviewSites(urls);
            setState(() {
              _results = data;
              _isLoading = false;
            });
          } 
        } catch (e) {
          debugPrint(e.toString());
        } finally {
          setState(() { _isLoading = false; });
        }
      });

      reader.readAsText(file);
    });
  }

  List<String> _extractUrls(String content, String extension) {
    final urlPattern = RegExp(
      r'(https?:\/\/[^\s]+)',
      caseSensitive: false,
      multiLine: true,
    );

    final matches = urlPattern.allMatches(content);
    
    List<String> urls = matches.map((match) => match.group(0)!).toList();
    
    return urls;
  }

  bool isValidUrl(String url) {
    if (url.isEmpty) {
      return false;
    }
    String urlWithScheme = url;
    if (!urlWithScheme.startsWith('http://') && !urlWithScheme.startsWith('https://')) {
      urlWithScheme = 'http://$urlWithScheme';
    }
    
    Uri? uri = Uri.tryParse(urlWithScheme);
    return uri != null && (uri.hasAbsolutePath || uri.hasAuthority);
  }
  
  void _onSearchPressed() async {
    try {
      _results.clear();
      setState(() { _isLoading = true; });

      List<String> urls = _urlController.text
          .split(',')
          .map((url) => url.trim())
          .where((url) => url.isNotEmpty)
          .toList();

      List<String> validUrls = urls.where((url) => isValidUrl(url)).toList();

      if (validUrls.isNotEmpty) {
        final data = await Fetch.fetchReviewSites(validUrls);
        setState(() {
          _results = data;
        });
      }
    } catch (e) {
      debugPrint(e.toString());
    } finally {
      setState(() { _isLoading = false; });
    } 
  }


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: NestedScrollView(
        physics: _results.isEmpty 
            ? const NeverScrollableScrollPhysics()
            : null,
        headerSliverBuilder: (context, innerBoxIsScrolled) {
          return [  
            SliverOverlapAbsorber(
              handle: NestedScrollView.sliverOverlapAbsorberHandleFor(context),
              sliver: SliverAppBar(
                expandedHeight: _results.isEmpty 
                    ? MediaQuery.of(context).size.height / 2
                    : 100,
                flexibleSpace: FlexibleSpaceBar(
                  background: Align(
                    alignment: Alignment.bottomCenter,
                    child: SearchBar(
                      controller: _urlController,
                      padding: const WidgetStatePropertyAll<EdgeInsets>(
                              EdgeInsets.symmetric(horizontal: 16.0)),
                      keyboardType: TextInputType.url,
                      hintText: 'Введите URL',
                      leading: IconButton(
                        onPressed: _onSearchPressed, 
                        icon: const Icon(Icons.search)
                      ),
                      trailing: <Widget>[
                        Tooltip(
                          message: 'Выберите csv или txt файл',
                          child: IconButton(
                            onPressed: _pickFile,
                            icon: const Icon(Icons.attach_file),
                          ),
                        )
                      ],
                      onSubmitted: (value) => _onSearchPressed(),
                    ),
                  ),
                ),
              ),
            ),
          ];
        },
        body: Column(
          children: [
            if (_isLoading)
              const SizedBox(height: 20,),

            if (_isLoading)
              const Center(child: CircularProgressIndicator()),

            Padding(
              padding: const EdgeInsets.all(8.0),
              child: Center(
                child: Container(
                  padding: const EdgeInsets.symmetric(vertical: 16.0),
                  width: MediaQuery.of(context).size.width < 800 ? MediaQuery.of(context).size.width : 800,
                  child: Wrap(
                    spacing: 8.0,
                    runSpacing: 8.0,
                    children: _results.map((result) {
                      return ConstrainedBox(
                        constraints: const BoxConstraints(
                          maxWidth: 200,
                          maxHeight: 30,
                        ),
                        child: Tooltip(
                          message: _results.indexOf(result).toString(),
                          child: ElevatedButton(
                            onPressed: () {
                              _pageController.animateToPage(
                                  _results.indexOf(result), 
                                  duration: const Duration(milliseconds: 400),
                                  curve: Curves.easeInOut,
                              );
                            },
                            child: Text(
                              result.url,
                              maxLines: 1,
                            ),
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                ),
              )
            ),
            Expanded(
              child: PageView.builder(
                controller: _pageController,
                itemCount: _results.length,
                itemBuilder: (context, index) {
                  return CustomScrollView(
                    key: PageStorageKey<String>(index.toString()),
                    slivers: [
                      SliverList(
                        delegate: SliverChildBuilderDelegate(
                          childCount: 8,
                          (BuildContext context, int sectionIndex) {
                            var sections = [
                              Column(
                                children: [
                                  Text(
                                    _results[index].url,
                                    style: Theme.of(context).textTheme.headlineMedium!.copyWith(
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                  const SizedBox(height: 8),
                                  Text(
                                    'Общая оценка: ${_results[index].totalScore.toStringAsFixed(2)}',
                                    style: Theme.of(context).textTheme.titleMedium,
                                  ),
                                ],
                              ),
                              Section(
                                title: 'Полная функциональность с помощью клавиатуры',
                                score: _results[index].keyboardFunctionality.toStringAsFixed(2),
                                recommendations: _results[index].keyboardFunctionalityRecom,
                              ),
                              Section(
                                title: 'Читаемость и управляемость для программ экранного доступа', 
                                score: _results[index].screenReaderAccessibility.toStringAsFixed(2), 
                                recommendations: _results[index].screenReaderAccessibilityRecom,
                              ),
                              Section(
                                title: 'Доступная капча', 
                                score: _results[index].captchaAccessibility.toStringAsFixed(2), 
                                recommendations: _results[index].captchaAccessibilityRecom,
                              ),
                              Section(
                                title: 'Описание заголовков и ссылок', 
                                score: _results[index].headingsLinksDescription.toStringAsFixed(2), 
                                recommendations: _results[index].headingsLinksDescriptionRecom,
                              ),
                              Section(
                                title: 'Достаточная контрастность', 
                                score: _results[index].contrast.toStringAsFixed(2), 
                                recommendations: _results[index].contrastRecom,
                              ),
                              Section(
                                title: 'Корректное масштабирование', 
                                score: _results[index].scalability.toStringAsFixed(2), 
                                recommendations: _results[index].scalabilityRecom,
                              ),
                              Section(
                                title: 'Альтернативный текст и текстовое описание изображения', 
                                score: _results[index].altText.toStringAsFixed(2), 
                                recommendations: _results[index].altTextRecom,
                              ),
                            ];
                            return Padding(
                              padding: const EdgeInsets.symmetric(vertical: 8.0),
                              child: Center(
                                child: SizedBox(
                                  width: MediaQuery.of(context).size.width < 800 ? MediaQuery.of(context).size.width : 800,
                                  child: sections[sectionIndex]
                                )
                              ),
                            );
                          },
                        ),
                      ),
                    ]
                  );
                }
              ),
            ),
          ],
        )
      )
    );
  }
}