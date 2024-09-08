FROM ubuntu:latest AS build-env

RUN apt-get update
RUN apt-get install -y curl git unzip

ARG FLUTTER_VERSION=latest
ARG FLUTTER_SDK_LOCATION=/usr/local/flutter
ARG APP_LOCATION=/app/

RUN git clone https://github.com/flutter/flutter.git $FLUTTER_SDK_LOCATION

ENV PATH="$FLUTTER_SDK_LOCATION/bin:$FLUTTER_SDK_LOCATION/bin/cache/dart-sdk/bin:${PATH}"

RUN flutter doctor -v

RUN mkdir $APP_LOCATION
COPY . $APP_LOCATION
WORKDIR $APP_LOCATION

RUN flutter clean
RUN flutter pub get
RUN flutter build web


FROM nginx

# COPY ../nginx.conf /etc/nginx/nginx.conf
COPY --from=build-env /app/build/web /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]