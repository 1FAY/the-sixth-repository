import 'package:flutter/material.dart';

import 'pages/home_page.dart';
import 'themes/theme.dart';
import 'utils/util.dart';


class App extends StatelessWidget {
  const App({ super.key });

  @override
  Widget build(BuildContext context) {
    final brightness = View.of(context).platformDispatcher.platformBrightness;
    TextTheme textTheme = createTextTheme(context, "Open Sans", "Roboto");

    MaterialTheme theme = MaterialTheme(textTheme);
    return MaterialApp(
      title: 'Flutter Demo',
      theme: brightness == Brightness.light ? theme.light() : theme.dark(),
      home: const HomePage()
    );
  }
}