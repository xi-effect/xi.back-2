import logging
from collections.abc import Iterator
from datetime import timedelta
from typing import ClassVar, Final

from pydantic import AwareDatetime, BaseModel

from app.common.config_bdg import notifications_bridge
from app.common.fastapi_ext import APIRouterExt
from app.common.schemas.notifications_sch import (
    ClassroomParticipantRecipientFilterSchema,
    NotificationInputV2Schema,
    NotificationKind,
    PersistedClassroomEventInstanceNotificationPayloadSchema,
    RepeatedClassroomEventInstanceNotificationPayloadSchema,
)
from app.common.utils.datetime import datetime_utc_now
from app.scheduler.routes.classroom_schedules_rst import (
    BaseEventInstanceListAdapter,
    build_classroom_schedule_adapter,
)

router = APIRouterExt(tags=["event reminders"])


class EventReminderSearchRequestSchema(BaseModel):
    happens_after: AwareDatetime
    happens_before: AwareDatetime


class EventInstanceReminderListAdapter(BaseEventInstanceListAdapter):
    default_idempotency_ttl: ClassVar[timedelta] = timedelta(hours=1)

    def generate_idempotency_expires_at(self) -> AwareDatetime:
        return datetime_utc_now() + self.default_idempotency_ttl

    def iter_sole_event_instance_notifications(
        self,
    ) -> Iterator[NotificationInputV2Schema]:
        for sole_event_instance in self.sole_event_instances:
            event = self.events_by_id[sole_event_instance.event_id]
            yield NotificationInputV2Schema(
                payload=PersistedClassroomEventInstanceNotificationPayloadSchema(
                    kind=NotificationKind.PERSISTED_CLASSROOM_EVENT_INSTANCE_REMINDER_V1,
                    classroom_id=event.classroom_id,
                    event_instance_id=sole_event_instance.id,
                ),
                recipient_filters=[
                    ClassroomParticipantRecipientFilterSchema(
                        classroom_id=event.classroom_id,
                        role=None,
                    )
                ],
                idempotency_key=str(sole_event_instance.id),
                idempotency_expires_at=self.generate_idempotency_expires_at(),
            )

    def iter_persisted_repeated_event_instance_notifications(
        self,
    ) -> Iterator[NotificationInputV2Schema]:
        for (
            persisted_repeated_event_instance
        ) in self.persisted_repeated_event_instances:
            event = self.events_by_id[persisted_repeated_event_instance.event_id]
            yield NotificationInputV2Schema(
                payload=PersistedClassroomEventInstanceNotificationPayloadSchema(
                    kind=NotificationKind.PERSISTED_CLASSROOM_EVENT_INSTANCE_REMINDER_V1,
                    classroom_id=event.classroom_id,
                    event_instance_id=persisted_repeated_event_instance.id,
                ),
                recipient_filters=[
                    ClassroomParticipantRecipientFilterSchema(
                        classroom_id=event.classroom_id,
                        role=None,
                    )
                ],
                idempotency_key=str(persisted_repeated_event_instance.id),
                idempotency_expires_at=self.generate_idempotency_expires_at(),
            )

    def iter_virtual_repeated_event_instance_notifications(
        self,
    ) -> Iterator[NotificationInputV2Schema]:
        for (
            virtual_repeated_event_instance_key,
            virtual_repeated_event_instance_value,
        ) in self.virtual_repeated_instances_by_id.items():
            if (
                virtual_repeated_event_instance_key
                in self.persisted_repeated_event_instance_keys
            ):
                continue

            event = self.events_by_id[virtual_repeated_event_instance_value.event_id]
            yield NotificationInputV2Schema(
                payload=RepeatedClassroomEventInstanceNotificationPayloadSchema(
                    kind=NotificationKind.REPEATED_CLASSROOM_EVENT_INSTANCE_REMINDER_V1,
                    classroom_id=event.classroom_id,
                    repetition_mode_id=virtual_repeated_event_instance_key.repetition_mode_id,
                    instance_index=virtual_repeated_event_instance_key.instance_index,
                ),
                recipient_filters=[
                    ClassroomParticipantRecipientFilterSchema(
                        classroom_id=event.classroom_id,
                        role=None,
                    )
                ],
                idempotency_key=(
                    f"{virtual_repeated_event_instance_key.repetition_mode_id}:"
                    f"{virtual_repeated_event_instance_key.instance_index}"
                ),
                idempotency_expires_at=self.generate_idempotency_expires_at(),
            )

    def iter_notifications(self) -> Iterator[NotificationInputV2Schema]:
        yield from self.iter_sole_event_instance_notifications()
        yield from self.iter_persisted_repeated_event_instance_notifications()
        yield from self.iter_virtual_repeated_event_instance_notifications()


REMINDERS_PER_REQUEST_SOFT_LIMIT: Final[int] = 20
REMINDERS_PER_REQUEST_HARD_LIMIT: Final[int] = 100


@router.post(
    path="/event-reminders/",
    summary="Queue sending all event reminders in a specific time period",
)
async def queue_sending_event_reminders(data: EventReminderSearchRequestSchema) -> None:
    # TODO currently this is called by a cron, but should be migrated to a better system
    # TODO make this more generic via the notification service itself

    schedule_adapter = (
        await build_classroom_schedule_adapter(  # TODO (170) proper service
            classroom_ids=None,
            happens_after=data.happens_after,
            happens_before=data.happens_before,
            adapter_type=EventInstanceReminderListAdapter,
            include_already_started_instances=False,
        )
    )
    for i, notification in enumerate(schedule_adapter.iter_notifications()):
        await notifications_bridge.send_notification(data=notification)
        if i == REMINDERS_PER_REQUEST_SOFT_LIMIT:
            logging.error(
                "Reached the soft limit of reminders in one request",
                extra={"request_data": data},
            )
        if i == REMINDERS_PER_REQUEST_HARD_LIMIT:
            logging.error(
                "Reached the hard limit of reminders in one request",
                extra={"request_data": data},
            )
            break
