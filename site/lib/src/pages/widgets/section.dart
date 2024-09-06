import 'package:flutter/material.dart';
import 'package:site/src/pages/widgets/html.dart';

import '../../data/accessibility_data.dart';

class Section extends StatelessWidget {
  const Section({ 
    super.key, 
    required this.title, 
    required this.score, 
    required this.recommendations 
  });

  final String title;
  final String score;
  final List<Recommendation> recommendations;

  @override
  Widget build(BuildContext context) {    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text(
              "$title: ",
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 16.0,
              ),
            ),
            Text(
              score,
              style: Theme.of(context).textTheme.titleMedium,
            ),
          ],
        ),
        if (recommendations.isNotEmpty) ...[
          const SizedBox(height: 8.0),
          ...recommendations.map((rec) {
            return Padding(
              padding: const EdgeInsets.symmetric(vertical: 4.0),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.info_outline, size: 20.0, color: Colors.blue),
                  const SizedBox(width: 8.0),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Html(htmlCode: rec.html),
                        Text('Рекомендации: ${rec.recom}'),
                      ],
                    ),
                  ),
                ],
              ),
            );
          }),
        ],
      ],
    );
  }
}