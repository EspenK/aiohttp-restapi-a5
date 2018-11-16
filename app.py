import ipaddress

from aiohttp import web
import json
import random
from functools import reduce
from hashlib import md5

sessions = {}
pending_tasks = {}
results_dict = {}


async def results(request: web.Request):
    session_id = int(request.path[len('/results/'):])
    if not await valid_session_id(session_id):
        return await valid_session_id(session_id)

    results_dict[session_id]['results'].append(['Feedback requested', 10])

    total_result = sum(result[1] for result in results_dict[session_id]['results'])
    response_object = {
        'student': 'Student Studentsen',
        'totalResult': total_result,
        'passed': True,
        'results': results_dict.get(session_id).get('results')
    }
    return web.Response(text=json.dumps(response_object), status=200, content_type='application/json')


async def auth(request: web.Request):
    random_number = random.randint(1, 100000)
    while random_number in sessions.values():
        random_number = random.randint(1, 100000)
    session_id = random_number

    if len(sessions) != 0:
        highest_user_id = max(sessions, key=int)
        user_id = int(highest_user_id) + 1
    else:
        user_id = 1

    sessions[user_id] = session_id
    results_dict[session_id] = {'userId': user_id,
                                'sessionId': session_id,
                                'has_requested_task': False,
                                'results': [['Successfully authorized', 20]]}

    response_object = {'success': True, 'sessionId': session_id, 'userId': user_id, 'comment': ''}
    return web.Response(text=json.dumps(response_object), status=200, content_type='application/json')


async def get_task(request: web.Request):
    session_id = await get_param(request, 'sessionId')
    if type(session_id) != web.Response:
        session_id = int(session_id)

    if not await valid_session_id(session_id):
        return await valid_session_id(session_id)

    if not results_dict[session_id]['has_requested_task']:
        results_dict[session_id]['has_requested_task'] = True
        results_dict[session_id]['results'].append(['Successfully requested a task', 10])

    task_nr = int(request.path[len('/gettask/'):])

    if task_nr == 1:
        response_object = await get_task1(request, session_id)
    elif task_nr == 2:
        response_object = await get_task2(request, session_id)
    elif task_nr == 3:
        response_object = await get_task3(request, session_id)
    elif task_nr == 4:
        response_object = await get_task4(request, session_id)
    elif task_nr == 2016:
        response_object = await get_secret_task(request, session_id)
    else:
        response_object = {'success': False, 'comment': 'Invalid task Id. P.S. How about trying sqrt(4064256)? ;)'}

    return web.Response(text=json.dumps(response_object), status=200, content_type='application/json')


async def get_task1(request: web.Request, session_id: int) -> dict:
    response_object = {'taskNr': 1,
                       'description': 'Task 1: You should send an HTTP POST with a JSON object containing'
                                      ' static message as a response to this task: include field msg=Hello '
                                      'in the JSON object',
                       'arguments': []}

    pending_tasks[session_id] = {'task': response_object,
                                 'answer': 'Hello'}
    return response_object


async def get_task2(request: web.Request, session_id: int) -> dict:
    quotes = [
        'Talk is cheap. Show me the code. - Linus Torvalds',
        'Programs must be written for people to read, and only incidentally for machines to execute. - Harold Abelson',
        'Give a man a program, frustrate him for a day. Teach a man to program, frustrate him for a lifetime. - Muhammad Waseem',
        'Not all roots are buried down in the ground, some are at the top of a tree. - Jinvirle'
    ]
    quote = quotes[random.randint(0, len(quotes) - 1)]
    response_object = {'taskNr': 2,
                       'description': 'You should read the text which is in the arguments[0] and echo it back: '
                                      'send an HTTP post with a field msg=receivedMessage',
                       'arguments': [quote]}

    pending_tasks[session_id] = {'task': response_object,
                                 'answer': quote}
    return response_object


async def get_task3(request: web.Request, session_id: int) -> dict:
    numbers = [random.randint(1, 100) for number in range(0, random.randint(1, 5))]
    product = reduce((lambda x, y: x * y), numbers)

    response_object = {
        'taskNr': 3,
        'description': 'Extract all the arguments as numbers, multiply them, and send the result to the server as '
                       'an HTTP POST with JSON object containing fields result=X, where X is the multiplication product',
        'arguments': numbers
    }
    pending_tasks[session_id] = {'task': response_object,
                                 'answer': product}
    return response_object


async def get_task4(request: web.Request, session_id: int) -> dict:
    pin = random.randint(0, 9999)
    hash = md5(str(pin).encode('utf-8')).hexdigest()
    response_object = {
        'taskNr': 4,
        'description': 'You should crack the four-digit PIN code, fromthe given md5 hash of it, which is in the '
                       'argument[0] and send an HTTP post with a parameter pin=XXXX. Note that the original pin was '
                       'treated as a String! E.g, for pin code 1234, MD5(�1234�) was calculated!',
        'arguments': [hash]}
    pending_tasks[session_id] = {'task': response_object,
                                 'answer': pin}
    return response_object


async def get_secret_task(request: web.Request, session_id: int) -> dict:
    address_str = f'192.168.{random.randint(0, 255)}.0'
    netmask_int = random.randint(24, 31)
    network = ipaddress.IPv4Network(f'{address_str}/{netmask_int}')

    response_object = {
        'taskNr': 2016,
        'description': 'Extract all the arguments as numbers, multiply them, and send the result to the server as '
                       'an HTTP POST with JSON object containing fields result=X, where X is the multiplication product',
        'arguments': [address_str, str(network.netmask)]
    }

    pending_tasks[session_id] = {'task': response_object,
                                 'answer': network}
    return response_object


async def solve(request: web.Request):
    data = await request.json()
    session_id = await get_data(data, 'sessionId')
    task = pending_tasks.get(session_id).get('task')
    answer = pending_tasks.get(session_id).get('answer')
    task_nr = task.get('taskNr')

    if task_nr == 1:
        msg = await get_data(data, 'msg')
        if msg.lower() == answer.lower():
            response_object = {'success': True, 'comment': f'Task {task_nr} solved!'}
            results_dict[session_id]['results'].append(['Task 1 solved!', 10])
        else:
            response_object = {'success': False, 'comment': f'Partly correct (5 points out of 10): We were '
                                                            f'expecting POST parameter msg=Hello, '
                                                            f'but got msg={msg}'}
            results_dict[session_id]['results'].append(['Task 1 solved!', 5])

    elif task_nr == 2:
        msg = await get_data(data, 'msg')
        if msg == answer:
            response_object = {'success': True, 'comment': f'Task {task_nr} solved!'}
            results_dict[session_id]['results'].append([f'Task {task_nr} solved!', 10])
        else:
            response_object = {'success': False, 'comment': f'Wrong value for msg.'}

    elif task_nr == 3:
        result = await get_data(data, 'result')

        if result == answer:
            response_object = {'success': True, 'comment': f'Task {task_nr} solved!'}
            results_dict[session_id]['results'].append([f'Task {task_nr} solved!', 20])
        else:
            response_object = {'success': False, 'comment': f'Wrong sum!'}

    elif task_nr == 4:
        result = await get_data(data, 'pin')
        if result == answer:
            response_object = {'success': True, 'comment': f'Task {task_nr} solved!'}
            results_dict[session_id]['results'].append([f'Task {task_nr} solved!', 40])
        else:
            response_object = {'success': False, 'comment': f'Wrong pin!'}

    elif task_nr == 2016:
        result = await get_data(data, 'ip')
        if result in result:
            response_object = {'success': True, 'comment': f'Secret task solved!'}
            results_dict[session_id]['results'].append([f'Secret task solved!', 80])
        else:
            response_object = {'success': False, 'comment': f'Wrong ip!'}

    else:
        response_object = {'success': False, 'comment': f'Invalid taskNr!'}

    return web.Response(text=json.dumps(response_object), status=200, content_type='application/json')


async def get_param(request: web.Request, param):
    try:
        value = request.query[param]
    except KeyError as e:
        response_object = {'success': False, 'comment': f'KeyError: {e}'}
        return web.Response(text=json.dumps(response_object), status=500, content_type='application/json')
    else:
        return value


async def get_data(data, param):
    try:
        value = data[param]
    except KeyError as e:
        response_object = {'success': False, 'comment': f'KeyError: {e}'}
        return web.Response(text=json.dumps(response_object), status=500, content_type='application/json')
    else:
        return value


async def valid_session_id(session_id: int):
    if session_id not in sessions.values():
        response_object = {'success': False, 'comment': 'Session ID is not valid'}
        return web.Response(text=json.dumps(response_object), status=200, content_type='application/json')
    else:
        return True


app = web.Application()
app.router.add_post('/auth', auth)
app.router.add_get('/gettask/{tail:.*}', get_task)
app.router.add_post('/solve', solve)
app.router.add_get('/results/{tail:.*}', results)

web.run_app(app)
