# ==============================================================================
# Dockerfile: pagos (Spring Boot 4.1 + Java 25)
# Multi-stage build with Temurin 25 JRE
# ==============================================================================
FROM maven:3.9.16-eclipse-temurin-25 AS builder

WORKDIR /build

# Cache maven dependencies
COPY pom.xml .
RUN mvn dependency:go-offline -B

# Copy source code and build runnable fat jar
COPY src ./src
RUN mvn clean package -DskipTests -B

# ==============================================================================
# Runner stage
# ==============================================================================
FROM eclipse-temurin:25-jre-jammy AS runner

ENV PORT=8002 \
    SPRING_PROFILES_ACTIVE=produccion

WORKDIR /app

# Non-root user
RUN groupadd -r spring && useradd -r -g spring spring

# Copy jar from builder stage
COPY --from=builder /build/target/*.jar app.jar

RUN chown -R spring:spring /app

USER spring

EXPOSE 8002

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://127.0.0.1:8002/actuator/health || exit 1

ENTRYPOINT ["java", "-XX:+UseG1GC", "-XX:MaxRAMPercentage=75.0", "-Djava.security.egd=file:/dev/./urandom", "-jar", "app.jar"]
