from flask import Flask, jsonify
import psycopg2
import threading
import time
import schedule
from secret import dbuser, dbpass, dbhost, dbport, dbdata


app = Flask(__name__)

EVENTSDB = []


@app.route('/search/<query>', methods=['GET'])
def search(query):
    results = []
    for event in EVENTSDB:
        if query in event["title"]:
            results.append(event)
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
            "SELECT e.name, scripture_reference, a.name, category_id, e.id FROM events e LEFT OUTER JOIN authors a ON e.author_id = a.id WHERE category_id <> 57 ORDER BY e.id DESC")
        events = cursor.fetchall()
        EVENTSDB.clear()
        for event in events:
            title = f"{event[0]} ({event[1]})"
            author = event[2]
            url = f"/category/messagelist/{event[3]}/{event[4]}"
            item = {
                "title": title,
                "author": author,
                "url": url
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
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=True)
