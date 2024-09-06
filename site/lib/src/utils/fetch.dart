import 'dart:convert';

import 'package:http/http.dart' as http;

import '../data/accessibility_data.dart';


class Fetch {
  static Future<List<AccessibilityData>> fetchSiteChecks(List<String> urls) async {
    final response = await http.post(
      Uri.parse('http://62.76.188.197:5000/check_sites'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'urls': urls}),
    );

    if (response.statusCode == 200) {
      final List<dynamic> jsonData = jsonDecode(response.body);
      return jsonData.map((item) => AccessibilityData.fromJson(item)).toList();
    } else {
      throw Exception('Failed to load site checks');
    }
  }
}