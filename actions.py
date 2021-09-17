import os
import time
from collections import OrderedDict

from data import Data
from logging_settings import set_logger


class Actions:

    @staticmethod
    def set_monitors_position_manually():
        monitors_data_from_xrandr = Data.get_monitors_data_from_xrandr()

        cables_ids_names = Actions.create_cable_id_cable_name_dict([*monitors_data_from_xrandr])

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
    def create_string_for_execute(monitors_data: list[str]):
        execute_command = []

        # TODO: сюда еще дописать логгирование: в xrandr нет указанного вами монитора: monitor_name
        xrandr_data = Data.get_monitors_data_from_xrandr()

        for id, cable_name in enumerate(monitors_data):
            if len(monitors_data) == id + 1:
                break

            """ 
            sometimes, on some devices, xrandr works better, if u will enter commands sequentially.
            so, its better to write command, each parts of which divided be |
            also, we creating command with top quality of each monitor
            """

            # TODO: первый аргумент в пользу данных из xrandr в формате словаря: можно будет спокойно получать информацию о мониторе по названию подключенного к нему кабеля. При использовании списка приходится юзать filter

            execute_command.append(
                f'xrandr --output {cable_name} --pos {xrandr_data[cable_name]["resolutions"][0]} --left-of {monitors_data[id + 1]} --pos {xrandr_data[monitors_data[id + 1]]["resolutions"][0]} | ')

        execute_command = ' '.join(execute_command)

        # cleaning spaces
        execute_command = execute_command[0: -3]

        return execute_command

    @staticmethod
    def create_cable_id_cable_name_dict(cables_names: list[str]):
        cables_ids_names = {id: cable for id, cable in enumerate(list(cables_names))}
        return cables_ids_names

    @staticmethod
    def create_layout_id_layout_name_dict(cables_layout: list[list[str]]):
        cables_ids_names = {id: [*monitors_position] for id, monitors_position in
                            enumerate(cables_layout)}

        return cables_ids_names

    @staticmethod
    def get_monitor_dimensions(monitor_dimensions):
        return monitor_dimensions[0] * monitor_dimensions[1]

    @staticmethod
    def match_monitor_with_cable():
        monitors_data_from_xrandr = Data.get_monitors_data_from_xrandr()

        # TODO: вот это у меня во многих местах встречается, нужно в отдельную функцию вынести

        cables_ids_names = Actions.create_cable_id_cable_name_dict(monitors_data_from_xrandr.keys())

        # TODO: вот это в отдельную функцию вынести, ибо используется в разных местах
        logger.info(
            f"\n\nВот список портов, к которым подключены мониторы в формате 'port_id --- port_name':\n"
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

        saved_cable_position_with_id = Actions.create_layout_id_layout_name_dict(saved_cables_positions)

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
    def connect_monitors_automatically(data_from_xrandr):
        if len(data_from_xrandr) > 1:
            monitors_sorted_by_size = list(OrderedDict(sorted(list(data_from_xrandr.items()),
                                                              key=lambda value: Actions.get_monitor_dimensions(
                                                                  value[1]['monitor_size']))).keys())
            # TODO: нужно описать кейсы, когда в этой функции вообще есть смысл
            # например, если скрипт начал работу на заднем плане. Чтоб хоть как-то моники подрубились... Удобнее работать?

            return monitors_sorted_by_size

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
