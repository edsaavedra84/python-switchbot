from __future__ import annotations
from abc import ABC

from typing import ClassVar, Dict, Optional

import humps

from switchbot.client import SwitchBotClient


class Remote:
    remote_type_for: ClassVar[Optional[str]] = None
    specialized_cls: ClassVar[Dict[str, Remote]] = {}

    def __init__(self, client: SwitchBotClient, id: str, **extra):
        self.client = client

        self.id: str = id
        self.name: str = extra.get('device_name')
        self.type: str = extra.get('remote_type')
        self.hub_id: str = extra.get('hub_device_id')

    def __init_subclass__(cls):
        if cls.remote_type_for is not None:
            cls.specialized_cls[cls.remote_type_for] = cls

    @classmethod
    def create(cls, client: SwitchBotClient, id: str, **extra):
        remote_type = extra.get('remote_type')
        if remote_type == 'Others':
            return OtherRemote(client, id=id, **extra)
        else:
            remote_cls = cls.specialized_cls.get(remote_type, SupportedRemote)
            return remote_cls(client, id=id, **extra)

    def command(self, action: str, parameter: Optional[str] = None, customize: Optional[bool] = False):
        parameter = 'default' if parameter is None else parameter
        command_type = 'customize' if customize else 'command'
        payload = humps.camelize({
            'command_type': command_type,
            'command': action if customize else humps.camelize(action),
            'parameter': parameter})
        
        self.client.post(f'devices/{self.id}/commands', json=payload)

    def __repr__(self):
        name = 'Remote' if self.type is None else self.type
        name = name.replace(' ', '')
        return f'{name}(id={self.id})'


class SupportedRemote(Remote):
    def turn(self, state: str):
        state = state.lower()
        assert state in ('on', 'off')
        self.command(f'turn_{state}')

class OtherRemote(Remote):
    remote_type_for = 'Others'

    def command(self, action: str, parameter: Optional[str] = None):
        super().command(action, parameter, True)
