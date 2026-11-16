import html

from app.common.schemas.classrooms_sch import ClassroomRole
from app.common.schemas.notifications_sch import (
    ClassroomNotificationPayloadSchema,
    EnrollmentNotificationPayloadSchema,
    EnrollmentV2NotificationPayloadSchema,
    InvitationAcceptanceNotificationPayloadSchema,
    InvitationAcceptanceV2NotificationPayloadSchema,
)
from app.notifications import texts
from app.notifications.services.notification_adapters.base_notification_adapter import (
    BaseNotificationAdapter,
)


class BaseClassroomOverviewNotificationAdapter[PayloadType](
    BaseNotificationAdapter[PayloadType]
):
    def build_classroom_overview_url(
        self,
        classroom_id: int,
        role: ClassroomRole,
    ) -> str:
        return self.build_url(
            path=f"/classrooms/{classroom_id}",
            params={"tab": "overview", "role": role},
        )


class IndividualInvitationAcceptedV1NotificationAdapter(
    BaseClassroomOverviewNotificationAdapter[
        InvitationAcceptanceNotificationPayloadSchema
    ]
):
    def adapt_button_text(self) -> str:
        return texts.INDIVIDUAL_INVITATION_ACCEPTED_V1_BUTTON_TEXT

    def adapt_button_link(self) -> str:
        return self.build_classroom_overview_url(
            self.payload.classroom_id,
            ClassroomRole.TUTOR,
        )

    def adapt_message_text(self) -> str:
        return texts.INDIVIDUAL_INVITATION_ACCEPTED_V1_MESSAGE

    def adapt_email_theme(self) -> str:
        return texts.INDIVIDUAL_INVITATION_ACCEPTED_V1_EMAIL_THEME

    def adapt_email_pre_header(self) -> str:
        return texts.INDIVIDUAL_INVITATION_ACCEPTED_V1_EMAIL_PRE_HEADER

    def adapt_email_header(self) -> str:
        return texts.INDIVIDUAL_INVITATION_ACCEPTED_V1_EMAIL_HEADER

    def adapt_email_content(self) -> str:
        return texts.INDIVIDUAL_INVITATION_ACCEPTED_V1_EMAIL_CONTENT


class GroupInvitationAcceptedV1NotificationAdapter(
    BaseClassroomOverviewNotificationAdapter[
        InvitationAcceptanceNotificationPayloadSchema
    ]
):
    def adapt_button_text(self) -> str:
        return texts.GROUP_INVITATION_ACCEPTED_V1_BUTTON_TEXT

    def adapt_button_link(self) -> str:
        return self.build_classroom_overview_url(
            self.payload.classroom_id,
            ClassroomRole.TUTOR,
        )

    def adapt_message_text(self) -> str:
        return texts.GROUP_INVITATION_ACCEPTED_V1_MESSAGE

    def adapt_email_theme(self) -> str:
        return texts.GROUP_INVITATION_ACCEPTED_V1_EMAIL_THEME

    def adapt_email_pre_header(self) -> str:
        return texts.GROUP_INVITATION_ACCEPTED_V1_EMAIL_PRE_HEADER

    def adapt_email_header(self) -> str:
        return texts.GROUP_INVITATION_ACCEPTED_V1_EMAIL_HEADER

    def adapt_email_content(self) -> str:
        return texts.GROUP_INVITATION_ACCEPTED_V1_EMAIL_CONTENT


class EnrollmentCreatedV1NotificationAdapter(
    BaseClassroomOverviewNotificationAdapter[EnrollmentNotificationPayloadSchema]
):
    def adapt_button_text(self) -> str:
        return texts.ENROLLMENT_CREATED_V1_BUTTON_TEXT

    def adapt_button_link(self) -> str:
        return self.build_classroom_overview_url(
            self.payload.classroom_id,
            ClassroomRole.STUDENT,
        )

    def adapt_message_text(self) -> str:
        return texts.ENROLLMENT_CREATED_V1_MESSAGE

    def adapt_email_theme(self) -> str:
        return texts.ENROLLMENT_CREATED_V1_EMAIL_THEME

    def adapt_email_pre_header(self) -> str:
        return texts.ENROLLMENT_CREATED_V1_EMAIL_PRE_HEADER

    def adapt_email_header(self) -> str:
        return texts.ENROLLMENT_CREATED_V1_EMAIL_HEADER

    def adapt_email_content(self) -> str:
        return texts.ENROLLMENT_CREATED_V1_EMAIL_CONTENT


class ClassroomConferenceStartedV1NotificationAdapter(
    BaseNotificationAdapter[ClassroomNotificationPayloadSchema]
):
    def adapt_button_text(self) -> str:
        return texts.CLASSROOM_CONFERENCE_STARTED_V1_BUTTON_TEXT

    def adapt_button_link(self) -> str:
        return self.build_url(
            path=f"/classrooms/{self.payload.classroom_id}",
            params={
                "tab": "overview",
                "role": ClassroomRole.STUDENT,
                "goto": "call",
            },
        )

    def adapt_message_text(self) -> str:
        return texts.CLASSROOM_CONFERENCE_STARTED_V1_MESSAGE

    def adapt_email_theme(self) -> str:
        return texts.CLASSROOM_CONFERENCE_STARTED_V1_EMAIL_THEME

    def adapt_email_pre_header(self) -> str:
        return texts.CLASSROOM_CONFERENCE_STARTED_V1_EMAIL_PRE_HEADER

    def adapt_email_header(self) -> str:
        return texts.CLASSROOM_CONFERENCE_STARTED_V1_EMAIL_HEADER

    def adapt_email_content(self) -> str:
        return texts.CLASSROOM_CONFERENCE_STARTED_V1_EMAIL_CONTENT


class IndividualInvitationAcceptedV2NotificationAdapter(
    BaseNotificationAdapter[InvitationAcceptanceV2NotificationPayloadSchema]
):
    def adapt_button_text(self) -> str:
        return texts.INDIVIDUAL_INVITATION_ACCEPTED_V2_BUTTON_TEXT

    def adapt_button_link(self) -> str:
        return self.build_url(
            path=f"/classrooms/{self.payload.classroom_id}",
            params={"tab": "schedule", "role": ClassroomRole.TUTOR},
        )

    def adapt_message_text(self) -> str:
        return texts.INDIVIDUAL_INVITATION_ACCEPTED_V2_MESSAGE_TEMPLATE.format(
            student_name=self.payload.student_name
        )

    def adapt_email_theme(self) -> str:
        return texts.INDIVIDUAL_INVITATION_ACCEPTED_V2_EMAIL_THEME_TEMPLATE.format(
            student_name=self.payload.student_name
        )

    def adapt_email_pre_header(self) -> str:
        return texts.INDIVIDUAL_INVITATION_ACCEPTED_V2_EMAIL_PRE_HEADER

    def adapt_email_header(self) -> str:
        return texts.INDIVIDUAL_INVITATION_ACCEPTED_V2_EMAIL_HEADER

    def adapt_email_content(self) -> str:
        return texts.INDIVIDUAL_INVITATION_ACCEPTED_V2_EMAIL_CONTENT_TEMPLATE.format(
            student_name=html.escape(self.payload.student_name)
        )


class GroupInvitationAcceptedV2NotificationAdapter(
    BaseClassroomOverviewNotificationAdapter[
        InvitationAcceptanceV2NotificationPayloadSchema
    ]
):
    def adapt_button_text(self) -> str:
        return texts.GROUP_INVITATION_ACCEPTED_V2_BUTTON_TEXT

    def adapt_button_link(self) -> str:
        return self.build_classroom_overview_url(
            self.payload.classroom_id,
            ClassroomRole.TUTOR,
        )

    def adapt_message_text(self) -> str:
        return texts.GROUP_INVITATION_ACCEPTED_V2_MESSAGE_TEMPLATE.format(
            student_name=self.payload.student_name
        )

    def adapt_email_theme(self) -> str:
        return texts.GROUP_INVITATION_ACCEPTED_V2_EMAIL_THEME

    def adapt_email_pre_header(self) -> str:
        return texts.GROUP_INVITATION_ACCEPTED_V2_EMAIL_PRE_HEADER

    def adapt_email_header(self) -> str:
        return texts.GROUP_INVITATION_ACCEPTED_V2_EMAIL_HEADER

    def adapt_email_content(self) -> str:
        return texts.GROUP_INVITATION_ACCEPTED_V2_EMAIL_CONTENT_TEMPLATE.format(
            student_name=html.escape(self.payload.student_name)
        )


class EnrollmentCreatedV2NotificationAdapter(
    BaseClassroomOverviewNotificationAdapter[EnrollmentV2NotificationPayloadSchema]
):
    def adapt_button_text(self) -> str:
        return texts.ENROLLMENT_CREATED_V2_BUTTON_TEXT

    def adapt_button_link(self) -> str:
        return self.build_classroom_overview_url(
            self.payload.classroom_id,
            ClassroomRole.STUDENT,
        )

    def adapt_message_text(self) -> str:
        return texts.ENROLLMENT_CREATED_V2_MESSAGE_TEMPLATE.format(
            group_name=self.payload.group_name
        )

    def adapt_email_theme(self) -> str:
        return texts.ENROLLMENT_CREATED_V2_EMAIL_THEME_TEMPLATE.format(
            group_name=self.payload.group_name
        )

    def adapt_email_pre_header(self) -> str:
        return texts.ENROLLMENT_CREATED_V2_EMAIL_PRE_HEADER

    def adapt_email_header(self) -> str:
        return texts.ENROLLMENT_CREATED_V2_EMAIL_HEADER

    def adapt_email_content(self) -> str:
        return texts.ENROLLMENT_CREATED_V2_EMAIL_CONTENT
