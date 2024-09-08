class AccessibilityData {
  final String url;
  final double totalScore;
  final double keyboardFunctionality;
  final List<Recommendation> keyboardFunctionalityRecom;
  final double screenReaderAccessibility;
  final List<Recommendation> screenReaderAccessibilityRecom;
  final double captchaAccessibility;
  final List<Recommendation> captchaAccessibilityRecom;
  final double headingsLinksDescription;
  final List<Recommendation> headingsLinksDescriptionRecom;
  final double contrast;
  final List<Recommendation> contrastRecom;
  final double scalability;
  final List<Recommendation> scalabilityRecom;
  final double altText;
  final List<Recommendation> altTextRecom;

  AccessibilityData({
    required this.url,
    required this.totalScore,
    required this.keyboardFunctionality,
    required this.keyboardFunctionalityRecom,
    required this.screenReaderAccessibility,
    required this.screenReaderAccessibilityRecom,
    required this.captchaAccessibility,
    required this.captchaAccessibilityRecom,
    required this.headingsLinksDescription,
    required this.headingsLinksDescriptionRecom,
    required this.contrast,
    required this.contrastRecom,
    required this.scalability,
    required this.scalabilityRecom,
    required this.altText,
    required this.altTextRecom,
  });

  factory AccessibilityData.fromJson(Map<String, dynamic> json) {
    List<Recommendation> keyboardFunctionalityRecom =
        (json['keyboard_functionality_recom'] as List)
            .map((e) => Recommendation.fromJson(e as Map<String, dynamic>))
            .toList();

    List<Recommendation> screenReaderAccessibilityRecom = 
        (json['screen_reader_accessibility_recom'] as List)
            .map((e) => Recommendation.fromJson(e as Map<String, dynamic>))
            .toList();

    List<Recommendation> captchaAccessibilityRecom =
        (json['captcha_accessibility_recom'] as List)
            .map((e) => Recommendation.fromJson(e as Map<String, dynamic>))
            .toList();

    List<Recommendation> headingsLinksDescriptionRecom = 
        (json['headings_links_description_recom'] as List)
            .map((e) => Recommendation.fromJson(e as Map<String, dynamic>))
            .toList();

    List<Recommendation> contrastRecom = 
        (json['contrast_recom'] as List)
            .map((e) => Recommendation.fromJson(e as Map<String, dynamic>))
            .toList();

    List<Recommendation> scalabilityRecom = 
        (json['scalability_recom'] as List)
            .map((e) => Recommendation.fromJson(e as Map<String, dynamic>))
            .toList();

    List<Recommendation> altTextRecom = 
        (json['alt_text_recom'] as List)
            .map((e) => Recommendation.fromJson(e as Map<String, dynamic>))
            .toList();

    return AccessibilityData(
      url: json['url'] as String,
      totalScore: json['total_score'] as double,
      keyboardFunctionality: json['keyboard_functionality'] as double,
      keyboardFunctionalityRecom: keyboardFunctionalityRecom,
      screenReaderAccessibility: json['screen_reader_accessibility'] as double,
      screenReaderAccessibilityRecom: screenReaderAccessibilityRecom,
      captchaAccessibility: json['captcha_accessibility'] as double,
      captchaAccessibilityRecom: captchaAccessibilityRecom,
      headingsLinksDescription: json['headings_links_description'] as double,
      headingsLinksDescriptionRecom: headingsLinksDescriptionRecom,
      contrast: json['contrast'] as double,
      contrastRecom: contrastRecom,
      scalability: json['scalability'] as double,
      scalabilityRecom: scalabilityRecom,
      altText: json['alt_text'] as double,
      altTextRecom: altTextRecom,
    );
  }
}

class Recommendation {
  final String html;
  final String recom;

  Recommendation({required this.html, required this.recom});

  factory Recommendation.fromJson(Map<String, dynamic> json) {
    return Recommendation(
      html: json['html'] as String,
      recom: json['recom'] as String,
    );
  }
}
