from flask import Flask, jsonify
from flask_cors import CORS
import psycopg2
import threading
import time
import schedule
from secret import dbuser, dbpass, dbhost, dbport, dbdata


app = Flask(__name__)
cors = CORS(app)

EVENTSDB = []


@app.route('/search/<query>', methods=['GET'])
def search(query):
    query = query.lower().strip()
    results = []
    limit = 10
    for event in EVENTSDB:
        if query in event["title"].lower():
            results.append(event)
            if len(results) == limit:
                break
    return jsonify(results)


def refreshdb():
    global EVENTSDB
    try:
        connection = psycopg2.connect(user=dbuser,
                                      password=dbpass,
                                      host=dbhost,
                                      port=dbport,
                                      database=dbdata)
        cursor = connection.cursor()
        cursor.execute(
            "SELECT e.name, scripture_reference, a.name, c.id, e.id, CONCAT_WS(' » ', et.name, eg.name, c.name) FROM events e LEFT OUTER JOIN categories c ON e.category_id = c.id LEFT OUTER JOIN event_groups eg ON c.event_group_id = eg.id LEFT OUTER JOIN event_types et ON eg.event_type_id = et.id LEFT OUTER JOIN authors a ON e.author_id = a.id WHERE category_id <> 57 ORDER BY e.id DESC")
        events = cursor.fetchall()
        EVENTSDB.clear()
        for event in events:
            title = event[0] or ""
            if event[1]:
                title += f" ({event[1]})"
            author = event[2] or ""
            url = f"/category/messagelist/{event[3]}/{event[4]}"
            id = event[4] or ""
            breadcrumbs = event[5] or ""
            item = {
                "id": id,
                "title": title,
                "author": author,
                "url": url,
                "breadcrumbs": breadcrumbs
            }
            EVENTSDB.append(item)

    except (Exception, psycopg2.Error) as error:
        print("Error", error)

    finally:
        if(connection):
            cursor.close()
            connection.close()


def scheduler():
    refreshdb()
    schedule.every(15).to(30).minutes.do(refreshdb)
    print("Task scheduled")
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    thread = threading.Thread(target=scheduler, daemon=True)
    thread.start()
    app.run(host='0.0.0.0', port=5000, threaded=True)
