implement a hybrid approach for your recipe app, you’ll combine raw SQL queries with an Object-Relational Mapping (ORM) tool like SQLAlchemy.

Database Connection optimization: Use connection pooling. This means you keep a pool of database connections open and reuse them instead of opening a new one for each query.Connection pooling improves performance by reducing the overhead of opening and closing connections.

SQL injection: using parameterized queries is a great security practice to avoid SQL injection.

Use ORM for most database interactions, as it reduces boilerplate code and integrates cleanly with Python objects.

Use Raw SQL for:
Complex queries involving joins or aggregates.
Queries where performance is critical.