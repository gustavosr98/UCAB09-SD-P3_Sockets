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
import signal
import threading
import time
import socket
import re
import logging
from hashlib import md5
import base64
from .config import Config


class EndloopIterException(Exception):
    """
    Excption para detener loop infinito
    """
    pass


class CommandErrorException(Exception):
    """
    Excption para lanzar al generarse un error en la ejecución del commando
    """
    def __init__(self, data):
        self.data = data


class UnvaUserException(CommandErrorException):

    def __init__(self):
        self.data = 'unvalidated user'


class Commnad(object):
    """
    Estructura de un objeto Commnad
    """
    def __init__(self, data):
        self.__name = None
        self.__params = []
        proc_data = data.strip('\n').strip('\r').split(' ')
        for part in proc_data:
            if part == '':
                continue
            if self.__name is None:
                self.__name = part
            else:
                self.__params.append(part)

    @property
    def name(self):
        return self.__name

    @property
    def params(self):
        return self.__params


class Response(object):
    """
    Estructura de un objeto de respuesta
    """
    def __init__(self, code, msg):
        self.__code = code
        self.__msg = msg

    @property
    def data(self):
        data = ('%s %s' % (self.__code, self.__msg)).strip()
        return (data + '\n').encode()


class OKResponse(Response):

    def __init__(self, msg=''):
        super(OKResponse, self).__init__('ok', msg)


class NOKResponse(Response):

    def __init__(self, msg):
        super(NOKResponse, self).__init__('error', msg)


class Server():

    INVALID_CMD_RESPONSE = NOKResponse('invalid command')
    BYE_RESPONSE = OKResponse('bye')

    def __init__(self):
        self.__conf = None
        self.__semaphore = None
        self.__sock = None
        self.__working = False

    @property
    def config(self):
        if self.__conf is None:
            self.__conf = Config()
        return self.__conf

    @property
    def semaphore(self):
        if self.__semaphore is None:
            max_conn = self.config.max_conn
            if not max_conn:
                max_conn = 20
            self.__semaphore = threading.Semaphore(max_conn)
        return self.__semaphore

    @property
    def server_sock(self):
        if self.__sock is None:
            socket.setdefaulttimeout(2.0)
            self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        return self.__sock

    @property
    def on_work(self):
        return self.__working

    def prepare(self):
        """
        Preparación del servidor
        """
        addr = self.config.bind_addr
        port = self.config.bind_port
        addr_port = (addr, port)
        logging.info('Iniciando servidor en %s:%s' % addr_port)
        trys = 0
        self.__working = True
        while self.on_work:
            try:
                self.server_sock.bind(addr_port)
                self.server_sock.listen(self.config.max_conn)
                break
            except OSError as exce:
                time.sleep(1)
                trys += 1
                logging.warn(
                    'Error en iniciar el servidor (%s) intento %d' % (
                        exce,
                        trys
                    )
                )
                time.sleep(1)
                continue

    def start(self):
        """
        Punto de partida de la ejecución del servidor
        """
        # manejo de la señal de finalización de ejecución
        signal.signal(signal.SIGINT, self.stop)
        # Configuración del logger
        logging.basicConfig(
            filename=self.config.log['filename'],
            level=getattr(logging, self.config.log['level']),
            format=self.config.log['format']
        )
        self.prepare()
        while self.on_work:
            # Loop infinito par aceptar conexiónes
            self.semaphore.acquire()
            conn = None
            try:
                conn = self.server_sock.accept()
            except socket.timeout:
                self.semaphore.release()
                continue
            if conn:
                th = threading.Thread(target=self.conn_worker, args=conn)
                th.start()
        self.server_sock.close()
        return 0

    def stop(self, sig, frame):
        """
        Manejo de salida del programa
        """
        if self.on_work:
            self.__working = False
            time.sleep(2)
            self.server_sock.close()
            exit(0)

    def conn_worker(self, client_sock, client_address):
        """
        Cuerpo de ejecución de un hilo
        """
        worker_data = {}
        r_ip, r_port = client_address
        logging.info(
            'Inicio de conexión desde %s:%s' % (
                r_ip,
                r_port
            )
        )
        while self.on_work:
            try:
                data = client_sock.recv(1024)
            except socket.timeout:
                continue
            except CommandErrorException as exc:
                logging.warn(
                    'Se produjo un error de conexión al recibir un mesaje'
                    ' desde %s:%s: %s' % (
                        r_ip,
                        r_port,
                        str(exc)
                    )
                )
                break
            commnad = Commnad(data.decode('utf-8'))
            cmd = self.get_srv_cmd(commnad)
            if not cmd:
                logging.warn(
                    'Comando (%s) invalido desde %s:%s' % (
                        commnad.name,
                        r_ip,
                        r_port
                    )
                )
                client_sock.send(self.INVALID_CMD_RESPONSE.data)
                break
            try:
                logging.warn(
                    'Comando (%s) desde %s:%s' % (
                        commnad.name,
                        r_ip,
                        r_port
                    )
                )
                response = cmd(commnad, client_sock, client_address,
                               worker_data)
                client_sock.send(response.data)
            except CommandErrorException as excep:
                logging.info(
                    'NOOK (%s) desde %s:%s' % (
                        excep.data,
                        r_ip,
                        r_port
                    )
                )
                client_sock.send(NOKResponse(excep.data).data)
                break
            except EndloopIterException:
                client_sock.send(self.BYE_RESPONSE.data)
                break
        logging.info(
            'Fin de conexión desde %s:%s' % (
                r_ip,
                r_port
            )
        )
        try:
            client_sock.shutdown(socket.SHUT_RDWR)
            client_sock.close()
        except Exception:
            pass
        self.semaphore.release()

    def get_srv_cmd(self, commnad):
        """
        Obtiene el metodo de ejecución de un command
        """
        method_name = 'srv_cmd_%s' % commnad.name
        if not hasattr(self, method_name):
            return False
        return getattr(self, method_name)

    def srv_cmd_bye(self, commnad, client_sock, client_address, worker_data):
        """
        Implementación del command(bye)
        """
        raise EndloopIterException()

    def srv_cmd_helloiam(self, commnad, client_sock, client_address,
                         worker_data):
        """
        Implementación del command(helloiam)
        """
        r_ip, _ = client_address
        user_name = None
        if len(commnad.params) > 0:
            user_name = commnad.params[0]
        if user_name is None or user_name not in self.config.users.keys():
            raise CommandErrorException('invalid user name')
        user_data = self.config.users[user_name]
        if user_data['ip'] != r_ip:
            raise CommandErrorException('invalid src ip')
        worker_data['user_data'] = user_data
        return OKResponse()

    def srv_cmd_msglen(self, commnad, client_sock, client_address,
                       worker_data):
        """
        Implementación del command(msglen)
        """
        if 'user_data' not in worker_data:
            raise UnvaUserException()

        user_data = worker_data['user_data']
        msg_len = len(user_data['msg'])
        return OKResponse('%d' % msg_len)

    def srv_cmd_chkmsg(self, commnad, client_sock, client_address,
                       worker_data):
        """
        Implementación del command(chkmsg)
        """
        usr_chksum = None
        if len(commnad.params) > 0:
            usr_chksum = commnad.params[0]
        if usr_chksum is None or len(usr_chksum) != 32 \
           or not re.findall(r'([a-f\d]{32})', usr_chksum):
            raise CommandErrorException('invalid checksum format')

        user_data = worker_data['user_data']
        msg = user_data['msg']

        md5meker = md5()
        md5meker.update(msg.encode('utf-8'))

        if usr_chksum != md5meker.hexdigest():
            raise CommandErrorException('bad checksum')

        return OKResponse()

    def srv_cmd_givememsg(self, commnad, client_sock, client_address,
                          worker_data):
        """
        Implementación del command(givememsg)
        """
        udp_port = None
        if len(commnad.params) > 0:
            udp_port = int(commnad.params[0])

        user_data = worker_data['user_data']
        msg = user_data['msg']
        r_ip, _ = client_address

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        data = base64.b64encode(msg.encode("utf-8"))
        sock.sendto(data, (r_ip, udp_port))

        return OKResponse()
