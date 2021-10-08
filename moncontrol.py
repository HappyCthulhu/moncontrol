import argparse
import json
import os
import time
from pathlib import Path

from card0_manager import CARD0
from logging_settings import set_logger
from monitors_manager import MONITORS
from xrandr_manager import XRANDR_MANAGER


# XRANDR_MANAGER, MONITOR_MANAGER, CARD0_MANAGER, LAUNCH
# CARD0_CONFIGS, MONITORS_LAYOUTS_CONFIGS, CONFIGS_MANAGER
# стоит ли создавать отдельный класс работы с конфигами, который наследовался в отдельные классы конфигов CARD0_CONFIGS и MONITORS_LAYOUTS_CONFIGS
# TODO: в режиме "auto-monitoring-connectivity": конец json-файла выглядит так: "/sys/class/drm/card0/card0-DP-1":
# думаю, это связано с отсутствием какого-то порта в принципе. Нужно None возвращать, а не пустое пространство
# очистить файл cables_conditions и запустить auto-monitoring. Баг пойман

# TODO: логгирование: dict doesnt contain position with this id!
# TODO: добавить Colorama для нормального консольного вывода
# TODO: начать писать тесты
# TODO: стоит ли заменить тыканье в shell на более профессиональные инструменты типа sh?
# TODO: оставшиеся TODO перевести на англ
# TODO: не отлавливает отключение всего одного монитора. Вроде фиксил, проверить
# TODO: наполнить текст комментариями
# TODO: у меня не реализован вариант, при котором произошло одновременное отключение одних и подключение других портов
# TODO: autorandr каким-то маническим образом позиционирует мои мониторы... Как?!
# TODO: точно ли мне нужна дополнительная информация о мониторах в конфигах? выглядит так, будто это просто слишком сильно усложняет скрипт... можно просто получить из xrandr инфу о соответствующем мониторе

def get_and_write_virtual_env():
    logger.info('Please install direnv!')

    with open('.envrc', 'w') as file:
        file.write('export CABLES_DIR=/sys/class/drm/card0/')

    with open('.env', 'w') as file:
        file.write('CABLES_DIR=/sys/class/drm/card0/')

    os.environ['CABLES_DIR'] = '/sys/class/drm/card0/'


def monitoring_activity():
    while True:
        CARD0.check_cable_conditions_until_it_change(CABLES_CONDITIONS_FILE_PATH)
        xrandr = XRANDR_MANAGER()

        # TODO: при пустом файлу st_size возвращает 1, а не 0... wtf
        print(Path(MONITORS_LAYOUTS_FILE_PATH).stat().st_size)

        if len(xrandr.monitors_data) == 1:
            execute_command = 'xrandr --auto'
            logger.info(execute_command)

        if not Path(MONITORS_LAYOUTS_FILE_PATH).is_file() or Path(MONITORS_LAYOUTS_FILE_PATH).stat().st_size < 2:
            position_manually()

        else:
            with open(MONITORS_LAYOUTS_FILE_PATH, 'r') as file:
                previously_saved_mons_pos = json.load(file)

            location_of_monitors = XRANDR_MANAGER.get_needed_monitors_layout_config_automatically(xrandr.monitors_data,
                                                                                                  previously_saved_mons_pos)

            if location_of_monitors:
                execute_command = xrandr.create_string_for_execute(xrandr.monitors_data, location_of_monitors)
                logger.debug(f'Позиционируем мониторы согласно сохраненным ранее настройкам: {location_of_monitors}')

                logger.info(execute_command)

            else:
                logger.info(
                    'Config with previous monitor layouts doesnt contains current connected cables. Connecting monitors with sorting by monitors size. If you want to set monitors by yout self, use command: "moncotrol -s"')
                monitors_sorted_by_size = MONITORS.connect_monitors_automatically(xrandr.monitors_data)

                with open(MONITORS_LAYOUTS_FILE_PATH, 'w') as file:
                    json.dump(monitors_sorted_by_size, file, indent=4)

                execute_command = xrandr.create_string_for_execute(xrandr.monitors_data, monitors_sorted_by_size)

                logger.info(execute_command)

        time.sleep(3)

        # os.system(execute_command)


def position_manually():
    monitors = MONITORS()
    xrandr = XRANDR_MANAGER()

    my_monitors_position = monitors.set_monitors_position_manually()

    # TODO: сделать проверку на существование и пустоту файла

    if not Path(MONITORS_LAYOUTS_FILE_PATH).is_file() or Path(MONITORS_LAYOUTS_FILE_PATH).stat().st_size < 2:

        with open(MONITORS_LAYOUTS_FILE_PATH, 'w') as file:
            json.dump([my_monitors_position], file)

        execute_command = XRANDR_MANAGER.create_string_for_execute(xrandr.monitors_data, my_monitors_position)

    else:
        with open(MONITORS_LAYOUTS_FILE_PATH, 'r') as file:
            previously_saved_mons_pos = json.load(file)

        new_collection_of_monitors_positions = xrandr.create_new_collections_of_mon_positions(my_monitors_position,
                                                                                              previously_saved_mons_pos)

        with open(MONITORS_LAYOUTS_FILE_PATH, 'w') as file:
            json.dump(new_collection_of_monitors_positions, file, indent=4)

        execute_command = XRANDR_MANAGER.create_string_for_execute(xrandr.monitors_data, new_collection_of_monitors_positions[0])

    logger.info('Settings was saved successfully')
    logger.info(execute_command)


def wrong_input(mode, settings):
    line_break = '\n'
    logger.critical(f'\nСкрипт не имеет настройки: {mode}\n\n'
                    f'\nЗапустите скрит с одной из следующих настроек:{line_break}{line_break}\n'
                    f'{f"{line_break}".join(settings)}')


def choose_one_of_saved_positions_of_monitors():
    if not Path(MONITORS_LAYOUTS_FILE_PATH).is_file() or Path(MONITORS_LAYOUTS_FILE_PATH).stat().st_size == 0:
        logger.info('Config file empty or doesnt exist')

    else:
        with open(MONITORS_LAYOUTS_FILE_PATH, 'r') as file:
            previously_saved_mons_pos = json.load(file)

        # TODO: возможно, стоит сделать отдельную функцию для принта конфигов
    if not previously_saved_mons_pos:
        logger.info('You did not save any monitors layouts yet')
    logger.info('Next strings will show monitors_positions in format: {config_id: [cable_1, cable_2, etc]}\n')

    saved_cable_position_with_id = XRANDR_MANAGER.create_layout_id_layout_name_dict(previously_saved_mons_pos)

    for id, monitors_names in saved_cable_position_with_id.items():
        print(f'\n{id}: {monitors_names}')

    print('\n')

    logger.info('Write number of config, that u need rn and press Enter button')
    input_id = int(input())

    xrandr = XRANDR_MANAGER()
    execute_command = xrandr.create_string_for_execute(xrandr.monitors_data, saved_cable_position_with_id[input_id])
    logger.info(execute_command)


def show_saved_monitors_positions():
    if not Path(MONITORS_LAYOUTS_FILE_PATH).is_file() or Path(MONITORS_LAYOUTS_FILE_PATH).stat().st_size == 0:
        logger.info('Config file empty or doesnt exist')

    else:
        with open(MONITORS_LAYOUTS_FILE_PATH, 'r') as file:
            saved_positions = json.load(file)

        saved_positions_with_position_id = XRANDR_MANAGER.create_layout_id_layout_name_dict(saved_positions)

        logger.info(
            'Next strings will show monitors_positions in format: {monitors_position_id: [cabel_1, cabel_2, etc]}')

        for id, monitors_names in saved_positions_with_position_id.items():
            print(f'\n{id}: {monitors_names}')
        print('\n')


def delete_config():
    if not Path(MONITORS_LAYOUTS_FILE_PATH).is_file() or Path(MONITORS_LAYOUTS_FILE_PATH).stat().st_size == 0:
        logger.info('Config file empty or doesnt exist: saved layouts doesnt exits')

    else:
        with open(MONITORS_LAYOUTS_FILE_PATH, 'r') as file:
            previously_saved_mons_pos = json.load(file)

    new_configs = MONITORS.delete_saved_config(previously_saved_mons_pos)

    with open(MONITORS_LAYOUTS_FILE_PATH, 'w') as file:
        json.dump(new_configs, file)

    logger.info(
        f'This configs was deleted successfully: {[config for config in previously_saved_mons_pos if config not in new_configs]}')


def make_parser():
    parser = argparse.ArgumentParser(description="Arguments:")
    parser.add_argument("-a", "--auto-monitoring-connectivity", default=False, action="store_true",
                        help='script will running permanently and check cabels connection. When condition of any cabel change, script will position monitors according to your previous settings.')
    parser.add_argument("-s", "--set-monitors-positions-manually", default=False, action="store_true",
                        help='in this mode u can position monitors (its position only in horizontal line now) much easier, comparing with xrandr')
    parser.add_argument("-c", "--choose-one-of-saved-positions-of-monitors", default=False, action="store_true",
                        help='You can pick one of yours previously saved monitors positions settings')
    parser.add_argument("-w", "--watch-saved-positions", default=False, action="store_true",
                        help='show you all previously saved positions of monitors')
    parser.add_argument("-m", "--match-monitor-with-cable", default=False, action="store_true",
                        help='this command will execute mode, that will help u understand, which monitor connected in specific port')
    parser.add_argument("-d", "--delete-saved-config", default=False, action="store_true",
                        help='delete certain previously saved configs')
    return parser


def start_app(mode):
    options = ['auto_monitoring_connectivity', 'set_monitors_positions_manually', 'match_monitor_with_cable',
               'watch_saved_positions', 'delete_saved_config', 'choose_one_of_saved_positions_of_monitors']
    start = {
        options[0]: monitoring_activity,
        options[1]: position_manually,
        options[2]: MONITORS.match_monitor_with_cable,
        options[3]: show_saved_monitors_positions,
        options[4]: delete_config,
        options[5]: choose_one_of_saved_positions_of_monitors
    }

    start[mode]()


if __name__ == '__main__':
    logger = set_logger()

    if not os.environ.get('CABLES_DIR'):
        get_and_write_virtual_env()

    MONITORS_LAYOUTS_FILE_PATH = 'my_monitor_layout.json'
    CABLES_CONDITIONS_FILE_PATH = 'cables_conditions_from_card0.json'

    args = make_parser().parse_args()
    my_gorgeous_dic = vars(args)
    mode = list(filter(lambda item: item[1], my_gorgeous_dic.items()))[0][0]

    start_app(mode)
