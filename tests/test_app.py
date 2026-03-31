"""Tests for the CLI app commands."""

from unittest.mock import patch

from typer.testing import CliRunner

from pydantic_wizard.app import app
from pydantic_wizard.exceptions import ConfigLoadError, ModelResolutionError

runner = CliRunner()


class TestNewCommand:
    @patch("pydantic_wizard.app.serialize_to_yaml")
    @patch("pydantic_wizard.app.questionary")
    @patch("pydantic_wizard.app.validate_and_fix")
    @patch("pydantic_wizard.app.prompt_model")
    @patch("pydantic_wizard.app.resolve_config_class")
    def test_new_config_success(
        self, mock_resolve, mock_prompt, mock_validate, mock_q, mock_serialize
    ):
        from pydantic import BaseModel

        class FakeModel(BaseModel):
            x: int = 1

        mock_resolve.return_value = FakeModel
        mock_prompt.return_value = {"x": 5}
        mock_validate.return_value = FakeModel(x=5)
        mock_q.confirm.return_value.ask.return_value = True

        result = runner.invoke(app, ["new", "fake.module.FakeModel"])
        assert result.exit_code == 0

    @patch("pydantic_wizard.app.resolve_config_class")
    def test_new_config_bad_model(self, mock_resolve):
        mock_resolve.side_effect = ModelResolutionError("not found")
        result = runner.invoke(app, ["new", "bad.Model"])
        assert result.exit_code == 1

    @patch("pydantic_wizard.app.validate_and_fix")
    @patch("pydantic_wizard.app.prompt_model")
    @patch("pydantic_wizard.app.resolve_config_class")
    def test_new_config_validation_fails(
        self, mock_resolve, mock_prompt, mock_validate
    ):
        from pydantic import BaseModel

        class FakeModel(BaseModel):
            x: int = 1

        mock_resolve.return_value = FakeModel
        mock_prompt.return_value = {"x": "bad"}
        mock_validate.return_value = None

        result = runner.invoke(app, ["new", "fake.module.FakeModel"])
        assert result.exit_code == 1

    @patch("pydantic_wizard.app.questionary")
    @patch("pydantic_wizard.app.validate_and_fix")
    @patch("pydantic_wizard.app.prompt_model")
    @patch("pydantic_wizard.app.resolve_config_class")
    def test_new_config_user_declines_save(
        self, mock_resolve, mock_prompt, mock_validate, mock_q
    ):
        from pydantic import BaseModel

        class FakeModel(BaseModel):
            x: int = 1

        mock_resolve.return_value = FakeModel
        mock_prompt.return_value = {"x": 5}
        mock_validate.return_value = FakeModel(x=5)
        mock_q.confirm.return_value.ask.return_value = False

        result = runner.invoke(app, ["new", "fake.module.FakeModel"])
        assert result.exit_code == 0


class TestValidateCommand:
    @patch("pydantic_wizard.app.resolve_config_class")
    @patch("pydantic_wizard.app.load_from_yaml")
    def test_validate_success(self, mock_load, mock_resolve, tmp_path):
        from pydantic import BaseModel

        class FakeModel(BaseModel):
            x: int = 1

        config_file = tmp_path / "config.yaml"
        config_file.write_text("x: 1")

        mock_load.return_value = ("FakeModel", "fake.FakeModel", {"x": 1})
        mock_resolve.return_value = FakeModel

        result = runner.invoke(app, ["validate", str(config_file)])
        assert result.exit_code == 0

    def test_validate_file_not_found(self):
        result = runner.invoke(app, ["validate", "/nonexistent/config.yaml"])
        assert result.exit_code == 1

    @patch("pydantic_wizard.app.load_from_yaml")
    def test_validate_no_model_class(self, mock_load, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("x: 1")
        mock_load.return_value = ("", "", {"x": 1})

        result = runner.invoke(app, ["validate", str(config_file)])
        assert result.exit_code == 1


class TestShowSchemaCommand:
    @patch("pydantic_wizard.app.resolve_config_class")
    def test_show_schema_bad_model(self, mock_resolve):
        mock_resolve.side_effect = ModelResolutionError("not found")
        result = runner.invoke(app, ["show-schema", "bad.Model"])
        assert result.exit_code == 1

    @patch("pydantic_wizard.app.resolve_config_class")
    def test_show_schema_success(self, mock_resolve):
        from pydantic import BaseModel, Field

        class FakeModel(BaseModel):
            name: str = Field(description="A name")
            count: int = 0

        mock_resolve.return_value = FakeModel
        result = runner.invoke(app, ["show-schema", "fake.FakeModel"])
        assert result.exit_code == 0


class TestEditCommand:
    def test_edit_file_not_found(self):
        result = runner.invoke(app, ["edit", "/nonexistent/config.yaml"])
        assert result.exit_code == 1

    @patch("pydantic_wizard.app.load_from_yaml")
    def test_edit_load_error(self, mock_load, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("x: 1")
        mock_load.side_effect = ConfigLoadError("parse error")

        result = runner.invoke(app, ["edit", str(config_file)])
        assert result.exit_code == 1

    @patch("pydantic_wizard.app.load_from_yaml")
    def test_edit_no_config_class(self, mock_load, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("x: 1")
        mock_load.return_value = ("", "", {"x": 1})

        result = runner.invoke(app, ["edit", str(config_file)])
        assert result.exit_code == 1
