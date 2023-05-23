# Copyright 2018-2023 contributors to the OpenLineage project
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING

import pytest

from openlineage.client import OpenLineageClient
from openlineage.client.run import Job, Run, RunEvent, RunState
from openlineage.client.serde import Serde
from openlineage.client.transport.kafka import KafkaConfig, KafkaTransport

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


def test_kafka_loads_full_config() -> None:
    config = KafkaConfig.from_dict(
        {
            "type": "kafka",
            "config": {"bootstrap.servers": "localhost:9092"},
            "topic": "random-topic",
            "flush": False,
        },
    )

    assert config.config["bootstrap.servers"] == "localhost:9092"
    assert config.topic == "random-topic"
    assert config.flush is False


def test_kafka_loads_partial_config_with_defaults() -> None:
    config = KafkaConfig.from_dict(
        {
            "type": "kafka",
            "config": {"bootstrap.servers": "localhost:9092"},
            "topic": "random-topic",
        },
    )

    assert config.config["bootstrap.servers"] == "localhost:9092"
    assert config.topic == "random-topic"
    assert config.flush is True


def test_kafka_load_config_fails_on_no_config() -> None:
    with pytest.raises(TypeError):
        KafkaConfig.from_dict(
            {
                "type": "kafka",
                "config": {"bootstrap.servers": "localhost:9092"},
            },
        )


def test_client_with_kafka_transport_emits(mocker: MockerFixture) -> None:
    mocker.patch("confluent_kafka.Producer")
    config = KafkaConfig(
        config={"bootstrap.servers": "localhost:9092"},
        topic="random-topic",
        flush=True,
    )
    transport = KafkaTransport(config)

    client = OpenLineageClient(transport=transport)
    event = RunEvent(
        eventType=RunState.START,
        eventTime=datetime.datetime.now().isoformat(),
        run=Run(runId=str(uuid.uuid4())),
        job=Job(namespace="kafka", name="test"),
        producer="prod",
    )

    client.emit(event)
    transport.producer.produce.assert_called_once_with(
        topic="random-topic",
        value=Serde.to_json(event).encode("utf-8"),
    )
    transport.producer.flush.assert_called_once()
