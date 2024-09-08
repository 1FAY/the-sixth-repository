import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter_web_plugins/url_strategy.dart';

import 'src/app.dart';


void main() async {
  await dotenv.load();
  
  usePathUrlStrategy();

  runApp(const App());
}


class Config {
  static String get apiUrl => dotenv.env['API_URL'] ?? 'http://localhost:5000';
}