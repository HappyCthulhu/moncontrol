import json
import os
import re
import subprocess
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
        monitors = subprocess.check_output('xrandr').decode()

        iterator = re.finditer(r"^\S[\W\w]*?(?=^(\S|$))", monitors, re.MULTILINE)
        monitors = [match.group() for match in iterator]
        connected_monitors = list(filter(lambda monitor_data: ' connected' in monitor_data, monitors))

        monitors_data = list(zip([monitor.split()[0] for monitor in connected_monitors], connected_monitors))
        physically_connected_monitors_data = {elem[0]: elem[1] for elem in monitors_data}

        data_from_xrandr_about_physically_connected_monitors = {}

        for port, data in physically_connected_monitors_data.items():
            resolutions = list(filter(lambda word: 'x' in word, ''.join(data.splitlines()[1:-1]).split()))

            monitor_size = data.splitlines()[0].split('y axis) ')[1]
            monitor_size = [int(option.replace('mm', '')) for option in monitor_size.split('x')]

            data_from_xrandr_about_physically_connected_monitors[port] = {'resolutions': resolutions,
                                                                          'monitor_size': monitor_size}

        return data_from_xrandr_about_physically_connected_monitors

    @staticmethod
    def get_needed_config_automatically(data_from_xrandr, saved_configs):
        # TODO: вот здесь нужно посмотреть, что происходит
        current_connection = set([elem for elem in [*data_from_xrandr]])

        for saved_config in saved_configs:
            if current_connection == set(saved_config):
                return saved_config

        return None

    @staticmethod
    def create_new_collections_of_mon_positions(new_mon_pos, previous_monitor_positions):

        for id, monitors_names_from_settings in enumerate(previous_monitor_positions):

            if monitors_names_from_settings == new_mon_pos:
                previous_monitor_positions.insert(0, previous_monitor_positions.pop(id))
                new_monitors_positions = previous_monitor_positions
                return new_monitors_positions

        previous_monitor_positions.insert(0, new_mon_pos)
        new_monitors_positions = previous_monitor_positions
        return new_monitors_positions


logger = set_logger()
