import argparse
import json
import os
import time
from pathlib import Path

from actions import Actions
from data import Data
from logging_settings import set_logger


# TODO: заменить тыканье в shell на более профессиональные инструменты
# TODO: оставшиеся TODO перевести на англ
# TODO: не отлавливает отключение всего одного монитора. Вроде фиксил, проверить
# TODO: наполнить текст комментариями
# TODO: у меня не реализован вариант, при котором произошло одновременное отключение одних и подключение других портов
# TODO: autorandr каким-то маническим образом позиционирует мои мониторы... Как?!
# TODO: возможно, эта функция в принципе не нужна, ведь мониторы определять будем согласно конфигу?
# TODO: дописать возможность изменения ориентации монитора на горизонтальную с последующим сохранением этого состояния

def get_and_write_virtual_env():
    logger.info('Please install direnv!')

    with open('.envrc', 'w') as file:
        file.write('export CABLES_DIR=/sys/class/drm/card0/')

    with open('.env', 'w') as file:
        file.write('CABLES_DIR=/sys/class/drm/card0/')

    os.environ['CABLES_DIR'] = '/sys/class/drm/card0/'



def monitoring_activity():
    while True:
        Data.check_for_changes_in_cable_conditions_until_it_change(CABLES_CONDITIONS_FILE_PATH)
        monitors_data_from_xrandr = Data.get_monitors_data_from_xrandr()

        if not Path(MONITORS_CONFIG_FILE_PATH).is_file() or Path(MONITORS_CONFIG_FILE_PATH).stat().st_size == 0:
            location_of_monitors = Actions.connect_monitors_automatically(monitors_data_from_xrandr,
                                                                          MONITORS_CONFIG_FILE_PATH)
            execute_command = Actions.create_string_for_execute(location_of_monitors)

        elif len(monitors_data_from_xrandr) == 1:
            execute_command = 'xrandr --auto'

        else:
            location_of_monitors = Data.search_for_current_mon_pos_in_previously_saved(monitors_data_from_xrandr,
                                                                                       MONITORS_CONFIG_FILE_PATH)
            if not location_of_monitors:
                location_of_monitors = Actions.connect_monitors_automatically(monitors_data_from_xrandr,
                                                                              MONITORS_CONFIG_FILE_PATH)

            execute_command = Actions.create_string_for_execute(location_of_monitors)
            logger.debug('Позиционируем мониторы согласно сохраненным ранее настройкам')
            # TODO: добавить возможность сохранять несколько разных позиций мониторов. Проверять, соответствует ли ныняшняя позиция одной из присутствующих в конфиге. Находить ее

        logger.info(execute_command)

        # os.system(execute_command)


def position_manually():
    my_monitors_position = Actions.set_monitors_position_manually()
    # TODO: add monitors_positions_to_my_monitors_layout.json
    found_monitors_pos = Data.search_for_current_mon_pos_in_previously_saved(my_monitors_position,
                                                                             MONITORS_CONFIG_FILE_PATH)

    with open(MONITORS_CONFIG_FILE_PATH, 'r') as file:
        previously_saved_mons_pos = json.load(file)

    if found_monitors_pos:
        # TODO: здесь необходимо сделать проверку, содержит ли файл настройку, содержащую такие же мониторы (порядок не важен). Если содержит: заменить на новые настройки. Если не содержит, просто добавить еще одну
        names_of_monitors_from_my_monitors_position = {[*mon_pos][0] for mon_pos in my_monitors_position}

        # TODO: это слишком сложный код
        config_that_consist_mon_pos_from_input = list(filter(
            lambda monitors_position: names_of_monitors_from_my_monitors_position == {[*monitor][0] for monitor in
                                                                                      monitors_position},
            previously_saved_mons_pos))
        for elem in config_that_consist_mon_pos_from_input:
            previously_saved_mons_pos.pop(previously_saved_mons_pos.index(elem))

    # TODO: добавляется внутри еще одного списка
    for_dumping = [my_monitors_position, *previously_saved_mons_pos]

    with open(MONITORS_CONFIG_FILE_PATH, 'w') as file:
        json.dump(for_dumping, file, indent=4)

    logger.info('Settings was saved successfully')


def wrong_input(mode, settings):
    line_break = '\n'
    logger.critical(f'\nСкрипт не имеет настройки: {mode}\n\n'
                    f'\nЗапустите скрит с одной из следующих настроек:{line_break}{line_break}\n'
                    f'{f"{line_break}".join(settings)}')


def show_saved_monitors_positions():
    saved_positions = Data.look_saved_monitors_position(MONITORS_CONFIG_FILE_PATH)
    if not saved_positions:
        logger.info('Config file empty or dont exist')

    else:
        saved_positions_with_position_id = [{id: monitors_position} for id, monitors_position in
                                            enumerate(saved_positions)]

        logger.info(
            'Next strings will show monitors_positions in format: {monitors_position_id: [cabel_1, cabel_2, etc]}')
        time.sleep(0.1)
        for monitor_id_position in saved_positions_with_position_id:
            print('\n')
            print(monitor_id_position)

        print('\n')


def delete_config():
    # TODO: проверить, как ведет себя этот конфиг при попытке удалить несколько мониторов за раз
    # TODO: понять, каким образом xrandr работает с мониторами и не сделать собственное управление без использования xrandr
    Actions.delete_saved_config(MONITORS_CONFIG_FILE_PATH)


def make_parser():
    parser = argparse.ArgumentParser(description="Arguments:")
    parser.add_argument("-m", "--monitoring-connectivity", default=False, action="store_true",
                        help='script will running permanently and check cabels connection. When condition of any cabel change, script will position monitors according to your previous settings.')
    parser.add_argument("-s", "--set-monitors-positions-manually", default=False, action="store_true",
                        help='in this mode u can position monitors (its position only in horizontal line now) much easier, comparing with xrandr')
    parser.add_argument("-c", "--match-monitor-with-cable", default=False, action="store_true",
                        help='this command will execute mode, that will help u understand, which monitor connected in specific port')
    parser.add_argument("-p", "--show-saved-positions", default=False, action="store_true",
                        help='show you all previously saved positions of monitors')
    parser.add_argument("-d", "--delete-saved-config", default=False, action="store_true",
                        help='delete certain previously saved configs')
    return parser


def start_app(mode):
    options = ['monitoring_connectivity', 'set_monitors_positions_manually', 'match_monitor_with_cable',
               'show_saved_positions', 'delete_saved_config']
    start = {
        options[0]: monitoring_activity,
        options[1]: position_manually,
        options[2]: Actions.match_monitor_with_cable,
        options[3]: show_saved_monitors_positions,
        options[4]: delete_config
    }

    start[mode]()



if __name__ == '__main__':
    logger = set_logger()

    if not os.environ.get('CABLES_DIR'):
        get_and_write_virtual_env()

    MONITORS_CONFIG_FILE_PATH = 'my_monitor_layout.json'
    CABLES_CONDITIONS_FILE_PATH = 'cables_conditions_from_card0.json'

    args = make_parser().parse_args()
    my_gorgeous_dic = vars(args)
    mode = list(filter(lambda item: item[1], my_gorgeous_dic.items()))[0][0]

    start_app(mode)
