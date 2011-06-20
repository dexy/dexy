import web
db = web.database(dbn='sqlite', db='testdb')
print db.insert("tasks", batch_id=12345)

