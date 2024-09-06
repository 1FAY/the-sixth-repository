import 'package:flutter/material.dart';


class Html extends StatefulWidget {
  const Html({ 
    super.key,
    required this.htmlCode,
  });

  final String htmlCode;

  @override
  State<Html> createState() => _HtmlState();
}

class _HtmlState extends State<Html> {
  bool _isExpanded = false;

  @override
  Widget build(BuildContext context) {
    return ExpansionTile(
      title: Text(
        _isExpanded ? 'HTML' : 'HTML: ${widget.htmlCode}',
        maxLines: 1,
      ),
      onExpansionChanged: (value) => setState(() { _isExpanded = !_isExpanded; }),
      children: [
        SelectableText(
          widget.htmlCode,
          style: const TextStyle(
            fontFamily: 'monospace',
          ),
        ),
      ],
    );
  }
}