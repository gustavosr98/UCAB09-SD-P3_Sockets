# -*- coding: utf-8 -*-
# Copyright (C) 2019 Romulo Rodriguez <rodriguezrjrr@gmail.com>
#
# This file is part of GetMyMsg.
#
# GetMyMsg is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# GetMyMsg is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Foobar.  If not, see <https://www.gnu.org/licenses/>.

import os.path
import yaml


class Config(object):
    '''
    Config Class
    '''
    __instance = None

    class __Config:

        __file_name = 'getmymsg.yaml'

        def __init__(self):
            file_name = Config.__Config.__file_name
            if not os.path.isfile(file_name):
                raise Exception('File {} not exist.'.format(file_name))
            stream = open(file_name, 'r')
            data = yaml.safe_load(stream)
            self.__validate__(data)
            self.__data = data
            stream.close()

        def __validate__(self, data):
            pass

        def __getattr__(self, name):
            return self.__data.get(name)

    def __new__(cls):
        if Config.__instance is None:
            Config.__instance = Config.__Config()
        return Config.__instance

    def __setattr__(self, *args, **kwargs):
        raise Exception('')

    def __getattr__(self, name):
        return getattr(Config.__instance, name)
