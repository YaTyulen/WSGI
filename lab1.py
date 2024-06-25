from wsgiref.simple_server import make_server
import pytz
import json
import datetime as dt


def app(environ, start_response):
    try:
        router = environ.get('PATH_INFO', '').lstrip('/')
        method = environ['REQUEST_METHOD']
        content = environ.get('CONTENT_LENGTH', '')

        try:
            if content:
                content = int(content)
            else:
                content = 0
        except ValueError:
            content = 0

        if content:
            request_body = environ['wsgi.input'].read(content)
        else:
            request_body = b''


        if method == 'GET':
            if router:
                try:
                    time_zone = pytz.timezone(router)
                except pytz.UnknownTimeZoneError:
                    start_response('400 Bad Request', [('Content-Type', 'text/html')])
                    return [b'Unknown timezone']
            else:
                time_zone = pytz.utc

            now_time = dt.datetime.now(time_zone) #текущее время в указанной зоне
            response_body =  f"<html><body style='display: flex; justify-content: center'><h1>Current time in {time_zone.zone} is {now_time.strftime('%B %d, %Y %H:%M:%S')}</h1></body></html>"
            start_response('200 OK', [('Content-Type', 'text/html')])
            return [response_body.encode('utf-8')]
        
        elif method == 'POST':
            if router == 'api/v1/convert':
                try:
                    incoming_json = json.loads(request_body)
                    date = incoming_json['date']
                    current_time_zone = pytz.timezone(incoming_json['tz'])
                    new_time_zone = pytz.timezone(incoming_json['target_tz'])

                    src_date = dt.datetime.strptime(date, '%m.%d.%Y %H:%M:%S')
                    src_date = current_time_zone.localize(src_date)
                    new_date = src_date.astimezone(new_time_zone)

                    response_body = json.dumps({"date": new_date.strftime('%B %d, %Y %H:%M:%S'), "time_zone": new_time_zone.zone})
                    start_response('200 OK', [('Content-Type', 'application/json')])
                    return [response_body.encode('utf-8')]

                except Exception as e:
                    start_response('400 Bad Request', [('Content-Type', 'application/json')])
                    return [json.dumps({"error": str(e)}).encode('utf-8')]

            elif router == 'api/v1/datediff':
                try:
                    incoming_json = json.loads(request_body)
                    first_date_str = incoming_json['first_date']
                    first_time_zone = pytz.timezone(incoming_json['first_tz'])
                    second_date_str = incoming_json['second_date']
                    second_time_zone = pytz.timezone(incoming_json['second_tz'])

                    first_date = first_time_zone.localize(dt.datetime.strptime(first_date_str, '%m.%d.%Y %H:%M:%S'))
                    second_date = second_time_zone.localize(dt.datetime.strptime(second_date_str, '%I:%M%p %Y-%m-%d'))
                    seconds = int((second_date - first_date).total_seconds())

                    response_body = json.dumps({"difference_in_seconds": seconds})
                    start_response('200 OK', [('Content-Type', 'application/json')])
                    return [response_body.encode('utf-8')]
                
                except Exception as e:
                    start_response('400 Bad Request', [('Content-Type', 'application/json')])
                    return [json.dumps({"error": str(e)}).encode('utf-8')]
                    

        start_response('404 Not Found', [('Content-Type', 'text/html')])
        return [b'Not Found']
    
    except Exception as e:
        start_response('500 Internal Server Error', [('Content-Type', 'text/html')])
        return [f'Internal Server Error: {str(e)}'.encode('utf-8')]


httpd = make_server('', 8000, app)
print("Serving on port 8000...")
httpd.serve_forever()
