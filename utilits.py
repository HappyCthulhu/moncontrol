import json
import os
import subprocess
import time
from pathlib import Path

from logging_settings import set_logger


def print_connected_cables(cabels_conditions):
    connected_cabels = []

    for cabel_path, condition in cabels_conditions.items():
        if condition == 'connected':
            connected_cabels.append(cabel_path.split('/')[-1])

    logger.debug(f'Подключены следующие кабели: {connected_cabels}')


# TODO: присылать сюда полный путь
def check_file_exist_or_not_empty(fp):
    # TODO: в других местах
    # TODO: добавить execute-команду, ибо без sudo не запускается
    # TODO: понять, какого черта пароль не кушает -S
    file_data = os.popen(f'cat {fp}', 'r').read()

    if not file_data:
        return False

    return True


def get_cabels_path_condition_from_card0():
    dirs = os.listdir(os.environ['CABELS_DIR'])
    cabel_dirs = list(filter(lambda path: 'HDMI' in path or 'DP' in path, dirs))
    cabels_path = [f'{os.environ["CABELS_DIR"]}{dir}' for dir in cabel_dirs]
    cabels_path_condition = {}
    for cabel_path in cabels_path:
        with open(f'{cabel_path}/status', 'r', encoding='utf-8') as file:
            cabels_path_condition[cabel_path] = file.read().replace('\n', '')

    return cabels_path_condition


def check_for_changes_in_cabel_conditions_until_it_change(cabels_conditions_file_path):
    new_cabels = []
    removed_cabels = []

    PATH_TO_CARD0 = '/sys/class/drm/card0'
    p = Path('.')
    PATH_TO_CURRENT_DIRECTORY = p.absolute()

    while True:
        if not check_file_exist_or_not_empty(f'{PATH_TO_CURRENT_DIRECTORY}/{cabels_conditions_file_path}'):
            logger.debug(f'Файл конфигов был пуст или не существовал: {new_cabels}')

            with open(cabels_conditions_file_path, 'w') as file:
                json.dump(get_cabels_path_condition_from_card0(), file)
            return True

        # TODO: у меня не реализован вариант, при котором произошло одновременное отключение одних и подключение других портов

        # TODO: нет файла конфигов - дамбим в файл конфиги и возвращаем True

        # TODO: есть файл конфигов - проверяем, изменилось ли что-то:
        ## TODO: если ничего не изменилось - принтим об этом инфу, дампим инфу в файлик и возвращаем True

        ## TODO: если что-то изменилось:
        ### TODO: если были подключены новые порты - принтим об этом инфу, дампим инфу в файлик и возвращаем True
        ### TODO: если были подключены новые порты - принтим об этом инфу, дампим инфу в файлик и возвращаем True

        else:
            time.sleep(1)
            with open(cabels_conditions_file_path, 'r') as file:
                past_cabels_conditions = json.load(file)

            # Проверяем, есть ли порты из предыдущего состояния в директориях:
            removed_cabels.clear()
            for port_path in list(past_cabels_conditions):
                if not check_file_exist_or_not_empty(f'{port_path}/status'):
                    removed_cabels.append(port_path.split("/")[-1])
                    # logger.debug(logger.debug_connected_cables(get_cabels_path_condition_from_card0()))
                    past_cabels_conditions.pop(port_path)

                    with open(cabels_conditions_file_path, 'w') as file:
                        json.dump(past_cabels_conditions, file)

                continue

            current_cabels_conditions_from_card0 = get_cabels_path_condition_from_card0()

            new_cabels.clear()
            for port_path, current_condition in current_cabels_conditions_from_card0.items():

                # Проверяем, не появился ли новый кабель в card0
                if not past_cabels_conditions.get(port_path):
                    new_cabels.append(port_path.split("/")[-1])

                    # logger.debug(logger.debug_connected_cables(current_cabels_conditions_from_card0))

                with open('cabels_conditions_from_card0.json', 'w') as file:
                    json.dump(current_cabels_conditions_from_card0, file)

                continue


            if new_cabels:
                logger.debug(f'Обнаружены новыe подключения: {new_cabels}')
                return True

            if removed_cabels:
                logger.debug(f'Следующие подключения были удалены: {removed_cabels}')
                return True

            logger.debug('Подключения портов не изменились')
        # TODO: выводить подключенные кабели


def get_monitors_data_from_xrandr():
    monitors_short_data = subprocess.check_output(['xrandr', '--listmonitors']).decode()
    monitors = subprocess.check_output('xrandr').decode()

    monitors_data = []
    for id, string in enumerate(monitors.splitlines()):

        # если строка начинается не с пробела
        # TODO: че за виртуальные мониторы и как их убрать из выдачи xrandr
        if string[0] != ' ' and ' connected' in string:

            # если следующая строка начинается с пробела
            if id < len(monitors.splitlines()) - 1:
                if monitors.splitlines()[id + 1][0] == ' ':
                    monitors_data.append(string)
                else:
                    continue

            else:
                # todo: ну вот последняя строка гипотетически может быть информацией о мониторе...
                break

        else:

            if id == 0:
                continue

            monitors_data[-1] = f'{monitors_data[-1]}\n{string}'


    monitors_data = list(zip([monitor.split()[0] for monitor in monitors_data], monitors_data))
    physically_connected_monitors_data = {elem[0]: elem[1] for elem in monitors_data}


    test = []

    for port, data in physically_connected_monitors_data.items():


        resolutions = list(filter(lambda word: 'x' in word, ''.join(data.splitlines()[1:-1]).split()))
        monitor_size = data.splitlines()[0].split('y axis) ')[1]
        monitor_size = [int(option.replace('mm', '')) for option in monitor_size.split('x')]
        test.append({port: {'resolutions': resolutions, 'monitor_size': monitor_size}})

    return test


def set_monitors_position_manually():
    monitors_data_from_xrandr = get_monitors_data_from_xrandr()
    # monitors_data_from_xrandr = test

    cabels_ids_names = {id: [*cabel][0] for id, cabel in enumerate(monitors_data_from_xrandr)}

    logger.info(
        f"\n\nВот список подключенных мониторов в формате 'monitor_id --- monitor_name':\n"
        f"{[f'{cabel_id} --- {cabel_name}' for cabel_id, cabel_name in cabels_ids_names.items()]}\n"
        f'\n'
        f'Ниже через запятую введите список в последовательности, которую вы хотели вы наблюдать:\n')
    # TODO: проверить инпут на верность (мб там лишние значения есть например)
    order_of_monitor_ids_from_input = [int(count) for count in input().strip().split(',')]

    ordered_monitors = []

    for monitor_id in order_of_monitor_ids_from_input:
        cabel_name = cabels_ids_names[monitor_id]
        monitor_data = list(filter(lambda elem: [*elem][0] == cabel_name, monitors_data_from_xrandr))[0]
        ordered_monitors.append(monitor_data)

    return ordered_monitors


def create_string_for_execute(monitors_data: list):
    reformat_to_dict = {}

    for monitor in monitors_data:
        reformat_to_dict = {**reformat_to_dict, **monitor}

    cabels_names = [[*cabel][0] for id, cabel in enumerate(monitors_data)]



    # execute_command = [
    #     f'xrandr --output {cabels_names.pop(0)}']
    #
    # for cabel_name in cabels_names:
    #
    #     execute_command.append(
    #         f'--left-of {cabel_name}')

    # TODO: обосанный xrandr не хочется принимать одним выражением строку с мониторами. Придется через | хуярить

    execute_command = []

    for id, cabel_name in enumerate(cabels_names):
        if len(cabels_names) == id + 1:
            break

        execute_command.append(
            f'xrandr --output {cabel_name} --left-of {cabels_names[id+1]} | ')



    execute_command = ' '.join(execute_command)


    execute_command = execute_command[0: -3]

    return execute_command

    # TODO: create_string_for_execute(ordered_monitors)


def get_monitor_product(monitor_dimensions):
    return monitor_dimensions[0] * monitor_dimensions[1]


# TODO: возможно, эта функция в принципе не нужна, ведь мониторы определять будем согласно конфигу?
def connect_monitors_automatically(data_from_xrandr):

    if len(data_from_xrandr) > 1:
        # TODO: сейчас сортирую по разрешению. Нужно по размеру сортировать, когда он прыгать не будет
        monitors_sorted_by_size= sorted(data_from_xrandr, key=lambda monitor: get_monitor_product(
            list(monitor.values())[0]['monitor_size']))
        monitor_with_lowest_size= [monitors_sorted_by_size.pop(0)]
        monitors_sorted_by_size.reverse()
        monitors_my_sort = [*monitor_with_lowest_size, *monitors_sorted_by_size]


        return monitors_my_sort

    else:
        os.system('xrandr --auto')
        return data_from_xrandr

logger = set_logger()
# TODO: дописать возможность изменения ориентации монитора на горизонтальную с последующим сохранением этого состояния


def match_monitor_with_cabel():
    monitors_data_from_xrandr = get_monitors_data_from_xrandr()


    cabels_ids_names = {id: [*cabel][0] for id, cabel in enumerate(monitors_data_from_xrandr)}

    # TODO: вот это в отдельную функцию вынести, ибо используется в разных местах
    logger.info(
        f"\n\nВот список портов, к которым подключенны мониторы в формате 'port_id --- port_name':\n"
        f"{[f'{cabel_id} --- {cabel_name}' for cabel_id, cabel_name in cabels_ids_names.items()]}\n"
        f'\n'
        f'Ниже введите id порта, чтобы узнать, какой монитор к нему подключен\n')
    # TODO: проверить инпут на верность (мб там лишние значения есть например)
    cabel_id_from_input = int(input().strip())

    logger.info('Сейчас на 3 секунды монитор, подключенный к выбранному вами кабелю поменяет яркость. Не прервайте работу скрипта!')

    string_for_execute = f'xrandr --output {cabels_ids_names[cabel_id_from_input]} --brightness 0.5'
    os.system(string_for_execute)
    time.sleep(3)

    string_for_execute = f'xrandr --output {cabels_ids_names[cabel_id_from_input]} --brightness 1'
    os.system(string_for_execute)


    logger.debug('Работа скрипта закончена')