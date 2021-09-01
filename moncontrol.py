import os
import time

import click

from logging_settings import set_logger
from utilits import check_for_changes_in_cabel_conditions_until_it_change, check_file_exist_or_not_empty, \
    connect_monitors_automatically, create_string_for_execute, set_monitors_position_manually, \
    get_monitors_data_from_xrandr, match_monitor_with_cabel, get_previous_monitor_position

# TODO: попробовать запускать с помощью poetry
# TODO: сохранять положения мониторов в файлик
# TODO: create_string_for_execute переодически выдает пустую строку
# TODO: сделать так, чтоб после мануальной настройки мониторов конфиги падали в json

def monitoring_activity():
    while True:
        check_for_changes_in_cabel_conditions_until_it_change(CABELS_CONDITIONS_FILE_PATH)
        monitors_data_from_xrandr = get_monitors_data_from_xrandr()

        if not check_file_exist_or_not_empty(MONITORS_CONFIG_FILE_PATH):

            location_of_monitors = connect_monitors_automatically(monitors_data_from_xrandr, MONITORS_CONFIG_FILE_PATH)
            execute_command = create_string_for_execute(location_of_monitors)

        elif len(monitors_data_from_xrandr) == 1:
            execute_command = 'xrandr --auto'

        else:
            location_of_monitors = get_previous_monitor_position(monitors_data_from_xrandr, MONITORS_CONFIG_FILE_PATH)
            if not location_of_monitors:
                location_of_monitors = connect_monitors_automatically(monitors_data_from_xrandr, MONITORS_CONFIG_FILE_PATH)
                
            execute_command = create_string_for_execute(location_of_monitors)
            logger.debug('Позиционируем мониторы согласно сохраненным ранее настройкам')
            # TODO: добавить возможность сохранять несколько разных позиций мониторов. Проверять, соответствует ли ныняшняя позиция одной из присутствующих в конфиге. Находить ее

        logger.info(execute_command)

        # os.system(execute_command)


def position_manually():
    my_monitors_position = set_monitors_position_manually()
    execute_command = create_string_for_execute(my_monitors_position)
    logger.info(execute_command)
    # os.system(execute_command)


def wrong_input(mode, settings):
    line_break = '\n'
    logger.critical(f'\nСкрипт не имеет настройки: {mode}\n\n'
                    f'\nЗапустите скрит с одной из следующих настроек:{line_break}{line_break}\n'
                    f'{f"{line_break}".join(settings)}')


@click.command()
@click.option('--mode', default='monitoring-connectivity', help='set_monitors_positions_manually: script will run permanently and check cabels connection. When condition of any cabel will change, script will position monitors according to your previous settings.')
@click.option('--mode', help='monitoring-connectivity: in this mode u can position monitors (its position only in horizontal line now) much easier, comparing with xrandr')
@click.option('--mode', help='match-monitor-with-cabel: this command will execute mode, that will help u understand, which monitor connected in specific port')
def start_app(mode):
    options = ['monitoring-connectivity', 'set_monitors_positions_manually', 'match-monitor-with-cabel']

    start = {
        'monitoring-connectivity': monitoring_activity,
        'set-monitors-positions-manually': position_manually,
        'match-monitor-with-cabel': match_monitor_with_cabel
    }

    if not start.get(mode):
        wrong_input(mode, options)

    else:
        start[mode]()


# TODO: подумать над красивым консольным выводом логгирования
# TODO: help приделать
# TODO: определение, какой монитор является каким
# TODO: приделать сохранение настроек в файл
# TODO: приделать возможность вызова сохраненных настроек из файла
# TODO: help должен вызываться

if __name__ == '__main__':
    logger = set_logger()

    MONITORS_CONFIG_FILE_PATH = 'my_monitor_layout.json'
    CABELS_CONDITIONS_FILE_PATH = 'cabels_conditions_from_card0.json'

    mode = start_app()

