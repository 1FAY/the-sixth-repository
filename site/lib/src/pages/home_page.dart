import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:path/path.dart' as path;

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
  // final ScrollController _scrollController = ScrollController();
  List<AccessibilityData> _results = [];

  bool _isLoading = false;

  Future<void> _pickFile() async {
    _results.clear();
    FilePickerResult? result = await FilePicker.platform.pickFiles(
      allowedExtensions: ['csv', 'txt'],
      type: FileType.custom,
    );

    if (result != null) {
      String? filePath = result.files.single.path;
      if (filePath != null) {
        print('Выбран файл: $filePath');
        
        String extension = path.extension(filePath).toLowerCase();
        
        String fileContent = await File(filePath).readAsString();
        
        List<String> urls = _extractUrls(fileContent, extension);
        await loadAccessibilityData(urls);
      }
    } else {
      print('Файл не был выбран');
    }

    if (result != null) {
      String? filePath = result.files.single.path;
      if (filePath != null) {
        print('Выбран файл: $filePath');
      }
    } else {
      print('Файл не был выбран');
    }
  }

  bool isValidUrl(String url) {
    String urlWithScheme = url;
    if (!urlWithScheme.startsWith('http://') && !urlWithScheme.startsWith('https://')) {
      urlWithScheme = 'http://$urlWithScheme';
    }
    
    Uri? uri = Uri.tryParse(urlWithScheme);
    return uri != null && (uri.hasAbsolutePath || uri.hasAuthority);
  }
  List<String> _extractUrls(String content, String extension) {
    List<String> urls = [];
    
    if (extension == '.csv') {
      List<String> lines = LineSplitter.split(content).toList();
      
      for (String line in lines) {
        urls.addAll(line.split(',').map((e) => e.trim()).where((e) => isValidUrl(e)));
      }
    } else if (extension == '.txt') {
      // Разделяем строки для TXT
      List<String> lines = LineSplitter.split(content).toList();
      
      // Предполагаем, что каждая строка содержит один URL
      for (String line in lines) {
        String trimmedLine = line.trim();
        if (isValidUrl(trimmedLine)) {
          urls.add(trimmedLine);
        }
      }
    }
    
    return urls;
  }


  void _scrollToIndex(int index) {
    // double position = index * 300.0;
    // _scrollController.animateTo(
    //   position,
    //   duration: const Duration(seconds: 1),
    //   curve: Curves.easeInOut,
    // );
  }

  Future<List<AccessibilityData>> loadAccessibilityData(List<String> url) async {
    // final jsonString = await rootBundle.loadString('test/data/test.json');
    // final List<dynamic> jsonList = json.decode(jsonString);
    // return jsonList.map((json) => AccessibilityData.fromJson(json)).toList();
    return await Fetch.fetchSiteChecks(url);
  }

  void _onSearchPressed() async {
    setState(() {
      _results.clear();
      _isLoading = true;
    });
    print(isValidUrl(_urlController.text));
    if (isValidUrl(_urlController.text)) {
      final data = await loadAccessibilityData([_urlController.text]);
      setState(() {
        _results = data;
        _isLoading = false;
      });
    } else {
      setState(() {
        _isLoading = false;
      });
    } 
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: CustomScrollView(
        slivers: [
          SliverAppBar(
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

          if (_isLoading)
            const SliverToBoxAdapter(
              child: SizedBox(height: 20,),
            ),

          if (_isLoading)
            const SliverToBoxAdapter(child: Center(child: CircularProgressIndicator())),

          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(8.0),
              child: LayoutBuilder(
                builder: (context, constraints) {
                  double width = constraints.maxWidth < 800 ? constraints.maxWidth : 800;
              
                  return Center(
                    child: Container(
                      padding: const EdgeInsets.symmetric(vertical: 16.0),
                      width: width,
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
                                  _scrollToIndex(_results.indexOf(result));
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
                  );
                }
              ),
            ),
          ),

          SliverList(
            delegate: SliverChildBuilderDelegate(
              childCount: _results.length,
              (context, index) {
                return LayoutBuilder(
                  builder: (context, constraints) {
                    double width = constraints.maxWidth < 800 ? constraints.maxWidth : 800;

                    return Center(
                      child: Card(
                        margin: const EdgeInsets.symmetric(vertical: 8.0, horizontal: 16.0),
                        elevation: 4.0,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12.0),
                        ),
                        child: SizedBox(
                          width: width,
                          child: Padding(
                            padding: const EdgeInsets.all(16.0),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  _results[index].url,
                                  style: Theme.of(context).textTheme.headlineMedium!.copyWith(
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                                const SizedBox(height: 8.0),
                                Text(
                                  'Общая оценка: ${_results[index].totalScore.toStringAsFixed(2)}',
                                  style: Theme.of(context).textTheme.titleMedium,
                                ),
                                const SizedBox(height: 8.0),
                                  Section(
                                    title: 'Полная функциональность с помощью клавиатуры', 
                                    score: _results[index].keyboardFunctionality.toStringAsFixed(2), 
                                    recommendations: _results[index].keyboardFunctionalityRecom
                                  ),
                                  const SizedBox(height: 8.0),
                                  Section(
                                    title: 'Читаемость и управляемость для программ экранного доступа', 
                                    score: _results[index].screenReaderAccessibility.toStringAsFixed(2), 
                                    recommendations: _results[index].screenReaderAccessibilityRecom,
                                  ),
                                  const SizedBox(height: 8.0),
                                  Section(
                                    title: 'Доступная капча', 
                                    score: _results[index].captchaAccessibility.toStringAsFixed(2), 
                                    recommendations: _results[index].captchaAccessibilityRecom,
                                  ),
                                  const SizedBox(height: 8.0),
                                  Section(
                                    title: 'Описание заголовков и ссылок', 
                                    score: _results[index].headingsLinksDescription.toStringAsFixed(2), 
                                    recommendations: _results[index].headingsLinksDescriptionRecom,
                                  ),
                                  const SizedBox(height: 8.0),
                                  Section(
                                    title: 'Достаточная контрастность', 
                                    score: _results[index].contrast.toStringAsFixed(2), 
                                    recommendations: _results[index].contrastRecom,
                                  ),
                                  const SizedBox(height: 8.0),
                                  Section(
                                    title: 'Корректное масштабирование', 
                                    score: _results[index].scalability.toStringAsFixed(2), 
                                    recommendations: _results[index].scalabilityRecom,
                                  ),
                                  const SizedBox(height: 8.0),
                                  Section(
                                    title: 'Альтернативный текст и текстовое описание изображения', 
                                    score: _results[index].altText.toStringAsFixed(2), 
                                    recommendations: _results[index].altTextRecom,
                                  ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    );
                  },
                );
              },
            ),
          ),
        ],
      )
    );
  }
}