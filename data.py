import json
import os
import subprocess
import time
from pathlib import Path

from logging_settings import set_logger


class Data:

    @staticmethod
    def check_cable_status(fp):
        if Path(fp).is_file():
            with open(fp, 'r') as file:
                status = file.read().replace('\n', '')
                return status

        else:
            return 'disconnected'

    @staticmethod
    def get_cables_path_condition_from_card0():
        dirs = os.listdir(os.environ['CABLES_DIR'])
        cables_dirs = list(filter(lambda path: 'HDMI' in path or 'DP' in path, dirs))
        cables_path = [f'{os.environ["CABLES_DIR"]}{dir}' for dir in cables_dirs]
        cables_path_condition = {}

        for cable_path in cables_path:
            with open(f'{cable_path}/status', 'r', encoding='utf-8') as file:
                cables_path_condition[cable_path] = file.read().replace('\n', '')

        return cables_path_condition

    @staticmethod
    def check_if_cable_was_disconnected(past_cables_conditions, cables_conditions_file_path):
        removed_cables = []

        # проходимся по списку из старых кабелей, отдельно получаем текущую информацию для кабеля, сравниваем
        for port_path, port_past_condition in past_cables_conditions.copy().items():
            current_cable_status = Data.check_cable_status(f'{port_path}/status').replace('\n', '')

            if current_cable_status != port_past_condition:
                removed_cables.append(port_path.split("/")[-1])
                past_cables_conditions[port_path] = current_cable_status

                # TODO: возможно стоит вынести это из функции. Просто возвращать не только removed_cables, но
                with open(cables_conditions_file_path, 'w') as file:
                    json.dump(past_cables_conditions, file, indent=4)

            # TODO: does this continue still needed?
            continue

        return removed_cables

    @staticmethod
    def check_if_cable_was_connected(past_cables_conditions, current_cables_conditions_from_card0):
        new_cables = []

        # проходимся по каждой кабелю из текущего состояния, смотрим, есть ли он в предыдущем состоянии
        for port_path, current_condition in current_cables_conditions_from_card0.items():

            # Проверяем, не появился ли новый кабель в card0
            if not past_cables_conditions.get(port_path):
                new_cables.append(port_path.split("/")[-1])

            continue

        return new_cables

    @staticmethod
    def check_for_changes_in_cable_conditions_until_it_change(cabels_conditions_file_path):

        p = Path('.')
        PATH_TO_CURRENT_DIRECTORY = p.absolute()

        while True:
            path_for_check = Path(f'{PATH_TO_CURRENT_DIRECTORY}/{cabels_conditions_file_path}')
            if not path_for_check.is_file() or path_for_check.stat().st_size == 0:
                logger.debug(f'Файл конфигов был пуст или не существовал')

                with open(cabels_conditions_file_path, 'w') as file:
                    json.dump(Data.get_cables_path_condition_from_card0(), file, indent=4)
                return True

            else:
                with open(cabels_conditions_file_path, 'r') as file:
                    past_cables_conditions = json.load(file)

                current_cables_conditions_from_card0 = Data.get_cables_path_condition_from_card0()

                cables_changes = {
                    'new_cables': Data.check_if_cable_was_connected(past_cables_conditions,
                                                                    current_cables_conditions_from_card0),
                    'removed_cables': Data.check_if_cable_was_disconnected(past_cables_conditions,
                                                                           cabels_conditions_file_path)
                }

                with open(cabels_conditions_file_path, 'w') as file:
                    json.dump(current_cables_conditions_from_card0, file, indent=4)

                if cables_changes['new_cables']:
                    logger.debug(f'Обнаружены новыe подключения: {cables_changes["new_cables"]}')
                    return True

                if cables_changes['removed_cables']:
                    logger.debug(f'Следующие подключения были удалены: {cables_changes["removed_cables"]}')
                    return True

                logger.debug('Подключения портов не изменились')

    @staticmethod
    def get_monitors_data_from_xrandr():
        time.sleep(3)
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

    # @staticmethod
    # def look_saved_monitors_position(fp):
    #     if not Path(fp).is_file() or Path(fp).stat().st_size == 0:
    #         return None
    #
    #     # TODO: при попытке мануального позиционрования, выдает ошибку, если файл конфигов пустой
    #     with open(fp, 'r') as file:
    #         saved_monitors_positions = json.load(file)
    #
    #     locations_of_monitors = []
    #
    #     for monitors_position in saved_monitors_positions:
    #         locations_of_monitors.append([[*monitor][0] for monitor in monitors_position])
    #
    #     return locations_of_monitors
    #
    @staticmethod
    def get_needed_config_automatically(data_from_xrandr, saved_configs):
        # TODO: точно ли не стоит data_from_xrandr возвращать в формате спика, а не словаря?
        current_connection = set([[*elem][0] for elem in data_from_xrandr])
        for saved_config in saved_configs:
            if current_connection == set(saved_config):
                return saved_config

    @staticmethod
    def create_new_collections_of_mon_positions(new_mon_pos, previous_monitor_positions):

        for id, monitors_names_from_settings in enumerate(previous_monitor_positions):

            if monitors_names_from_settings == new_mon_pos:
                previous_monitor_positions.insert(0, previous_monitor_positions.pop(id))
                new_monitors_positions =  previous_monitor_positions
                return new_monitors_positions

        previous_monitor_positions.insert(0, new_mon_pos)
        new_monitors_positions = previous_monitor_positions
        return new_monitors_positions


logger = set_logger()
