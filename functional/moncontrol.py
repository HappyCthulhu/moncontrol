import argparse
import os

from launch import Launch
from logging_settings import set_logger
from monitors_manager import Monitors


# TODO: создать bash-скрипт, который создает директорию конфигов, делает moncotrol executable, спрашивает, где лежит директория c проектом и добавляет в /bin
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
        options[0]: Launch.monitoring_activity,
        options[1]: Launch.position_manually,
        options[2]: Monitors.match_monitor_with_cable,
        options[3]: Launch.show_saved_monitors_positions,
        options[4]: Launch.delete_config,
        options[5]: Launch.choose_one_of_saved_positions_of_monitors
    }

    start[mode]()


if __name__ == '__main__':
    logger = set_logger()

    if not os.environ.get('CABLES_DIR'):
        get_and_write_virtual_env()

    args = make_parser().parse_args()
    my_gorgeous_dic = vars(args)
    mode = list(filter(lambda item: item[1], my_gorgeous_dic.items()))[0][0]

    start_app(mode)
