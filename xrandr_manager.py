import re
import subprocess


class XRANDR_MANAGER:
    def __init__(self):
        self.monitors_data = self.get_monitors_data()

    def get_monitors_data(self):
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
    def create_cable_id_cable_name_dict(cables_names: list[str]):
        # TODO: XRANDR_MANAGER. Почему? Это разве не действия с мониторами?
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
    def create_string_for_execute(xrandr_monitors_data, input_monitors_layout: list[str]):
        # TODO: XRANDR_MANAGER (приватная функция)
        execute_command = []

        # TODO: сюда еще дописать логгирование: в xrandr нет указанного вами монитора: monitor_name

        for id, cable_name in enumerate(input_monitors_layout):
            if len(input_monitors_layout) == id + 1:
                break

            """ 
            sometimes, on some devices, xrandr works better, if u will enter commands sequentially.
            so, its better to write command, each parts of which divided be |
            also, we creating command with top quality of each monitor
            """

            # TODO: первый аргумент в пользу данных из xrandr в формате словаря: можно будет спокойно получать информацию о мониторе по названию подключенного к нему кабеля. При использовании списка приходится юзать filter

            execute_command.append(
                f'xrandr --output {cable_name} --pos {xrandr_monitors_data[cable_name]["resolutions"][0]} --left-of {input_monitors_layout[id + 1]} --pos {xrandr_monitors_data[input_monitors_layout[id + 1]]["resolutions"][0]} | ')

        execute_command = ' '.join(execute_command)

        # cleaning spaces
        execute_command = execute_command[0: -3]

        return execute_command

    @staticmethod
    def get_needed_monitors_layout_config_automatically(data_from_xrandr, saved_configs):
        # TODO: вот здесь нужно посмотреть, что происходт
        # TODO: не очень понятно, к какому классу это стоит отнести
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

