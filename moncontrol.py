import json
import time

import click

from logging_settings import set_logger
from utilits import check_for_changes_in_cabel_conditions_until_it_change, check_file_exist_or_not_empty, \
    connect_monitors_automatically, create_string_for_execute, set_monitors_position_manually, \
    get_monitors_data_from_xrandr, match_monitor_with_cabel, search_for_current_mon_pos_in_previously_saved, \
    look_saved_monitors_position, delete_saved_config


# TODO: попробовать запускать с помощью poetry
# TODO: сохранять положения мониторов в файлик
# TODO: create_string_for_execute переодически выдает пустую строку
# TODO: сделать так, чтоб после мануальной настройки мониторов конфиги падали в json

def monitoring_activity():
    while True:
        check_for_changes_in_cabel_conditions_until_it_change(CABLES_CONDITIONS_FILE_PATH)
        monitors_data_from_xrandr = get_monitors_data_from_xrandr()

        if not check_file_exist_or_not_empty(MONITORS_CONFIG_FILE_PATH):

            location_of_monitors = connect_monitors_automatically(monitors_data_from_xrandr, MONITORS_CONFIG_FILE_PATH)
            execute_command = create_string_for_execute(location_of_monitors)

        elif len(monitors_data_from_xrandr) == 1:
            execute_command = 'xrandr --auto'

        else:
            location_of_monitors = search_for_current_mon_pos_in_previously_saved(monitors_data_from_xrandr,
                                                                                  MONITORS_CONFIG_FILE_PATH)
            if not location_of_monitors:
                location_of_monitors = connect_monitors_automatically(monitors_data_from_xrandr,
                                                                      MONITORS_CONFIG_FILE_PATH)

            execute_command = create_string_for_execute(location_of_monitors)
            logger.debug('Позиционируем мониторы согласно сохраненным ранее настройкам')
            # TODO: добавить возможность сохранять несколько разных позиций мониторов. Проверять, соответствует ли ныняшняя позиция одной из присутствующих в конфиге. Находить ее

        logger.info(execute_command)

        # os.system(execute_command)


def position_manually():
    my_monitors_position = set_monitors_position_manually()
    # TODO: add monitors_positions_to_my_monitors_layout.json
    found_monitors_pos = search_for_current_mon_pos_in_previously_saved(my_monitors_position, MONITORS_CONFIG_FILE_PATH)

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


# def delete_saved_config():
#     with open(MONITORS_CONFIG_FILE_PATH, 'r') as file:
#         previously_saved_mons_pos = json.load(file)
#
#     saved_cables_positions = []
#
#     for position in previously_saved_mons_pos:
#         cables_positions = []
#
#         for cable in position:
#             cables_positions.append([*cable][0])
#         saved_cables_positions.append(cables_positions)
#
#     saved_cable_position_with_id = {id: [*monitors_position] for id, monitors_position in
#                                     enumerate(saved_cables_positions)}
#
#     logger.info('Next strings will show monitors_positions in format: {config: [cabel_1, cabel_2, etc]}\n')
#     for id, monitors_names in saved_cable_position_with_id.items():
#         print(f'{id}: {monitors_names}')
#
#     logger.info('Write separate by commas ids of configs and script will delete them from saved configs')
#     input_ids = [int(id) for id in input().strip().split(', ')]
#
#     for id in input_ids:
#         cables_for_delete_from_input = saved_cable_position_with_id[id]
#         configs_for_dump = list(
#             filter(lambda config: cables_for_delete_from_input != [[*monitor][0] for monitor in config],
#                    previously_saved_mons_pos))
#
#     with open(MONITORS_CONFIG_FILE_PATH, 'w') as file:
#         json.dump(configs_for_dump, file)
#
#     logger.info(f'This configs was deleted successfully: {input_ids}')


def wrong_input(mode, settings):
    line_break = '\n'
    logger.critical(f'\nСкрипт не имеет настройки: {mode}\n\n'
                    f'\nЗапустите скрит с одной из следующих настроек:{line_break}{line_break}\n'
                    f'{f"{line_break}".join(settings)}')


def show_saved_monitors_positions():
    saved_positions = look_saved_monitors_position(MONITORS_CONFIG_FILE_PATH)
    if not saved_positions:
        logger.info('Config file empty or dont exist')

    else:
        saved_positions_with_position_id = [{id: monitors_position} for id, monitors_position in
                                            enumerate(saved_positions)]

        logger.info(
            'Next strings will show monitors_positions in format: {monitors_position_id: [cabel_1, cabel_2, etc]}')
        time.sleep(0.1)
        for monitor_id_position in saved_positions_with_position_id:
            print(monitor_id_position)
            # logger.info(json.dumps(saved_positions, indent=4))

def delete_config():
    delete_saved_config(MONITORS_CONFIG_FILE_PATH)

@click.command()
@click.option('--mode', default='monitoring-connectivity',
              help='set-monitors-positions-manually: script will run permanently and check cabels connection. When condition of any cabel will change, script will position monitors according to your previous settings.')
@click.option('--mode',
              help='monitoring-connectivity: in this mode u can position monitors (its position only in horizontal line now) much easier, comparing with xrandr')
@click.option('--mode',
              help='match-monitor-with-cabel: this command will execute mode, that will help u understand, which monitor connected in specific port')
@click.option('--mode', help='show-saved-positions: show you previously saved positions of monitors')
@click.option('--mode', help='delete-saved-config: u can choose configs, what you want delete')
def start_app(mode):
    options = ['monitoring-connectivity', 'set-monitors-positions-manually', 'match-monitor-with-cabel',
               'show-saved-positions', 'delete-saved-config']
    start = {
        options[0]: monitoring_activity,
        options[1]: position_manually,
        options[2]: match_monitor_with_cabel,
        options[3]: show_saved_monitors_positions,
        options[4]: delete_config
    }

    if not start.get(mode):
        wrong_input(mode, options)

    else:
        start[mode]()


if __name__ == '__main__':
    logger = set_logger()

    MONITORS_CONFIG_FILE_PATH = 'my_monitor_layout.json'
    CABLES_CONDITIONS_FILE_PATH = 'cabels_conditions_from_card0.json'

    mode = start_app()
