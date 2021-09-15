import json
import os
import time

from data import Data
from logging_settings import set_logger


class Actions:

    @staticmethod
    def set_monitors_position_manually():
        monitors_data_from_xrandr = Data.get_monitors_data_from_xrandr()

        cables_ids_names = {id: [*cable][0] for id, cable in enumerate(monitors_data_from_xrandr)}

        logger.info(
            f"\n\nВот список подключенных мониторов в формате 'monitor_id --- monitor_name':\n"
            f"{[f'{cable_id} --- {cable_name}' for cable_id, cable_name in cables_ids_names.items()]}\n"
            f'\n'
            f'Ниже через запятую введите список в последовательности, которую вы хотели вы наблюдать:\n')
        # TODO: проверить инпут на верность (мб там лишние значения есть например)
        order_of_monitor_ids_from_input = [int(count) for count in input().strip().split(',')]

        ordered_monitors = []

        for monitor_id in order_of_monitor_ids_from_input:
            cable_name = cables_ids_names[monitor_id]
            ordered_monitors.append(cable_name)

        return ordered_monitors

    @staticmethod
    def create_string_for_execute(monitors_data: list):


        """ 
        sometimes, on some devices, xrandr works better, if u will enter commands sequentially.
        so, its better to write command, each parts of which divided be |
        """
        execute_command = []

        for id, cable_name in enumerate(monitors_data):
            if len(monitors_data) == id + 1:
                break

            execute_command.append(
                f'xrandr --output {cable_name} --left-of {monitors_data[id + 1]} | ')

        execute_command = ' '.join(execute_command)

        execute_command = execute_command[0: -3]

        return execute_command

    @staticmethod
    def get_monitor_dimensions(monitor_dimensions):
        return monitor_dimensions[0] * monitor_dimensions[1]

    @staticmethod
    def match_monitor_with_cable():
        monitors_data_from_xrandr = Data.get_monitors_data_from_xrandr()

        cables_ids_names = {id: [*cable][0] for id, cable in enumerate(monitors_data_from_xrandr)}

        # TODO: вот это в отдельную функцию вынести, ибо используется в разных местах
        logger.info(
            f"\n\nВот список портов, к которым подключенны мониторы в формате 'port_id --- port_name':\n"
            f"{[f'{cable_id} --- {cable_name}' for cable_id, cable_name in cables_ids_names.items()]}\n"
            f'\n'
            f'Ниже введите id порта, чтобы узнать, какой монитор к нему подключен\n')
        # TODO: проверить инпут на верность (мб там лишние значения есть например)
        cable_id_from_input = int(input().strip())

        logger.info(
            'Сейчас на 3 секунды монитор, подключенный к выбранному вами кабелю поменяет яркость. Не прервайте работу скрипта!')

        string_for_execute = f'xrandr --output {cables_ids_names[cable_id_from_input]} --brightness 0.5'
        os.system(string_for_execute)

        time.sleep(3)

        string_for_execute = f'xrandr --output {cables_ids_names[cable_id_from_input]} --brightness 1'
        os.system(string_for_execute)

        logger.debug('Работа скрипта закончена')

    @staticmethod
    def delete_saved_config(saved_cables_positions):

        saved_cable_position_with_id = {id: [*monitors_position] for id, monitors_position in
                                        enumerate(saved_cables_positions)}

        logger.info('Next strings will show monitors_positions in format: {config: [cable_1, cable_2, etc]}\n')
        for id, monitors_names in saved_cable_position_with_id.items():
            print(f'\n{id}: {monitors_names}')

        logger.info('Write separate by commas ids of configs and script will delete them from saved configs')

        # filter is needed in case of string: "1, 2, "
        input_ids = [int(id) for id in list(filter(None, input().strip().split(',')))]
        configs_for_delete = [saved_cable_position_with_id[id] for id in input_ids]

        new_configs = []

        for saved_config in saved_cables_positions:
            if saved_config not in configs_for_delete:
                new_configs.append(saved_config)

        return new_configs


    @staticmethod
    def connect_monitors_automatically(data_from_xrandr, fp_to_config_file):
        if len(data_from_xrandr) > 1:
            monitors_sorted_by_size = sorted(data_from_xrandr, key=lambda monitor: Actions.get_monitor_dimensions(
                list(monitor.values())[0]['monitor_size']))
            monitor_with_lowest_size = [monitors_sorted_by_size.pop(0)]
            monitors_sorted_by_size.reverse()
            monitors_auto_sort = [*monitor_with_lowest_size, *monitors_sorted_by_size]

            # TODO: оно что, затирает придыдущие настройки?
            with open(fp_to_config_file, 'w') as file:
                json.dump([monitors_auto_sort], file, indent=4)

            return monitors_auto_sort

        else:
            os.system('xrandr --auto')
            return data_from_xrandr

    @staticmethod
    def print_connected_cables(cables_conditions):
        connected_cables = []

        for cable_path, condition in cables_conditions.items():
            if condition == 'connected':
                connected_cables.append(cable_path.split('/')[-1])

        logger.debug(f'Подключены следующие кабели: {connected_cables}')


logger = set_logger()
