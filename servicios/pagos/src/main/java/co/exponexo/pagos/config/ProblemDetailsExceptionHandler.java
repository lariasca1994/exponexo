package co.exponexo.pagos.config;

import jakarta.servlet.http.HttpServletRequest;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class ProblemDetailsExceptionHandler {

    @ExceptionHandler(ApiProblemException.class)
    public ResponseEntity<Map<String, Object>> handleProblemException(
            ApiProblemException ex,
            HttpServletRequest request
    ) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("type", ex.getProblemType());
        body.put("title", ex.getTitle());
        body.put("status", ex.getStatus());
        body.put("detail", ex.getMessage());
        body.put("instance", request.getRequestURI());
        Object corr = request.getAttribute(CorrelationIdFilter.ATTRIBUTE_NAME);
        if (corr != null) {
            body.put("correlacion_id", corr.toString());
        }
        return ResponseEntity
                .status(ex.getStatus())
                .contentType(MediaType.APPLICATION_PROBLEM_JSON)
                .body(body);
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, Object>> handleValidationException(
            MethodArgumentNotValidException ex,
            HttpServletRequest request
    ) {
        String detail = ex.getBindingResult().getFieldErrors().stream()
                .findFirst()
                .map(fe -> fe.getField() + ": " + fe.getDefaultMessage())
                .orElse("Datos de solicitud inválidos.");

        Map<String, Object> body = new LinkedHashMap<>();
        body.put("type", "https://exponexo.co/problemas/validacion");
        body.put("title", "Datos de solicitud inválidos");
        body.put("status", HttpStatus.UNPROCESSABLE_ENTITY.value());
        body.put("detail", detail);
        body.put("instance", request.getRequestURI());
        Object corr = request.getAttribute(CorrelationIdFilter.ATTRIBUTE_NAME);
        if (corr != null) {
            body.put("correlacion_id", corr.toString());
        }
        return ResponseEntity
                .status(HttpStatus.UNPROCESSABLE_ENTITY)
                .contentType(MediaType.APPLICATION_PROBLEM_JSON)
                .body(body);
    }
}
