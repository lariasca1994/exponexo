package co.exponexo.pagos.config;

public class ApiProblemException extends RuntimeException {

    private final int status;
    private final String title;
    private final String problemType;

    public ApiProblemException(int status, String title, String detail, String problemType) {
        super(detail);
        this.status = status;
        this.title = title;
        this.problemType = problemType;
    }

    public int getStatus() { return status; }
    public String getTitle() { return title; }
    public String getProblemType() { return problemType; }
}
