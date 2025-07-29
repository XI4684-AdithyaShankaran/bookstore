FROM bookstore-base-alpine:latest
COPY ./backend /app
WORKDIR /app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]