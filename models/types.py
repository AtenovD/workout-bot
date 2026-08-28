from sqlalchemy import BigInteger, Integer


sqlite_bigint_pk = BigInteger().with_variant(Integer, "sqlite")
