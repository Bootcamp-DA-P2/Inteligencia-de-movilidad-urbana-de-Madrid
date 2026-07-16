import duckdb
con = duckdb.connect("database/trafico.duckdb")

con.sql("SELECT COUNT(*), MIN(fecha), MAX(fecha) FROM raw_live").show()
con.sql("SELECT * FROM raw_live LIMIT 5").show()
con.sql("SELECT error, COUNT(*) FROM raw_live GROUP BY error").show()