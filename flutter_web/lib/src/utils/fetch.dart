import 'dart:convert';

import 'package:flutter_web/main.dart';
import 'package:http/http.dart' as http;

import '../data/accessibility_data.dart';


class Fetch {
  static Future<List<AccessibilityData>> fetchReviewSites(List<String> urls) async {
    final response = await http.post(
      Uri.parse('${Config.apiUrl}/review'),
      headers: {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
      body: jsonEncode({'urls': urls}),
    );

    if (response.statusCode == 200) {
      final List<dynamic> jsonData = jsonDecode(response.body);
      return jsonData.map((item) => AccessibilityData.fromJson(item)).toList();
    } else {
      throw Exception('Failed to load review');
    }
  }
}