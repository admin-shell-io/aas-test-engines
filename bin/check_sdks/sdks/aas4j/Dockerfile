FROM eclipse-temurin:19-jdk-jammy
RUN apt-get update && apt-get install -y --no-install-recommends \
    maven \
    && apt-get clean
WORKDIR /app
COPY src/pom.xml /app
