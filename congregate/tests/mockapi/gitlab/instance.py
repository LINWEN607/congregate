class MockInstanceApi():
    def get_appearance_configuration(self):
        return {
            "title": "",
            "description": "",
            "logo": None,
            "header_logo": None,
            "favicon": None,
            "new_project_guidelines": "",
            "profile_image_guidelines": "",
            "header_message": "",
            "footer_message": "",
            "message_background_color": "#E75E40",
            "message_font_color": "#FFFFFF",
            "email_header_and_footer_enabled": False
        }

    def get_appearance_configuration_403(self):
        return {
            "message": "403 Forbidden"
        }
