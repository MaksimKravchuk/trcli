import pytest

from tests.helpers.results_uploader_helper import (
    get_project_id_mocker,
    upload_results_inner_functions_mocker,
)
from tests.test_data.results_provider_test_data import (
    TEST_UPLOAD_RESULTS_FLOW_TEST_DATA,
    TEST_UPLOAD_RESULTS_FLOW_IDS,
    TEST_GET_SUITE_ID_PROMPTS_USER_TEST_DATA,
    TEST_GET_SUITE_ID_PROMPTS_USER_IDS,
    TEST_ADD_MISSING_SECTIONS_PROMPTS_USER_TEST_DATA,
    TEST_ADD_MISSING_SECTIONS_PROMPTS_USER_IDS,
    TEST_ADD_MISSING_TEST_CASES_PROMPTS_USER_TEST_DATA,
    TEST_ADD_MISSING_TEST_CATAS_PROMPTS_USER_IDS,
    TEST_GET_SUITE_ID_SINGLE_SUITE_MODE_BASELINES_TEST_DATA,
    TEST_GET_SUITE_ID_SINGLE_SUITE_MODE_BASELINES_IDS,
)
from trcli.api.results_uploader import ResultsUploader
from trcli.cli import Environment
from trcli.constants import FAULT_MAPPING, PROMPT_MESSAGES, SuiteModes
from trcli.readers.junit_xml import JunitParser
from trcli.constants import ProjectErrors


class TestResultsUploader:
    @pytest.fixture(scope="function")
    def result_uploader_data_provider(self, mocker):
        environment = mocker.patch("trcli.api.results_uploader.Environment")
        environment.host = "https://fake_host.com/"
        environment.project = "Fake project name"

        junit_file_parser = mocker.patch.object(JunitParser, "parse_file")
        api_request_handler = mocker.patch(
            "trcli.api.results_uploader.ApiRequestHandler"
        )
        results_uploader = ResultsUploader(
            environment=environment, result_file_parser=junit_file_parser
        )

        yield environment, api_request_handler, results_uploader

    @pytest.mark.results_uploader
    def test_project_name_missing_in_test_rail(
        self, result_uploader_data_provider, mocker
    ):
        """The purpose of this test is to check that proper message will be printed and trcli will terminate
        with proper code when project with name provided does not exist in TestRail."""
        (
            environment,
            api_request_handler,
            results_uploader,
        ) = result_uploader_data_provider
        exit_code = 1
        get_project_id_mocker(
            results_uploader=results_uploader,
            project_id=ProjectErrors.not_existing_project,
            error_message=f"{environment.project} project doesn't exists.",
            failing=True,
        )
        expected_log_calls = [
            mocker.call(f"{environment.project} project doesn't exists.")
        ]

        with pytest.raises(SystemExit) as exception:
            results_uploader.upload_results()

        environment.log.assert_has_calls(expected_log_calls)
        assert (
            exception.type == SystemExit
        ), f"Expected SystemExit exception, but got {exception.type} instead."
        assert (
            exception.value.code == exit_code
        ), f"Expected exit code {exit_code}, but got {exception.value.code} instead."

    @pytest.mark.results_uploader
    def test_error_during_checking_of_project(
        self, result_uploader_data_provider, mocker
    ):
        """The purpose of this test is to check that proper message would be printed and trcli tool will
        terminate with proper code when errors occurs during project name check."""
        (
            environment,
            api_request_handler,
            results_uploader,
        ) = result_uploader_data_provider
        exit_code = 1
        get_project_id_mocker(
            results_uploader=results_uploader,
            project_id=ProjectErrors.other_error,
            error_message="Unable to connect",
            failing=True,
        )
        expected_log_calls = [
            mocker.call(
                FAULT_MAPPING["error_checking_project"].format(
                    error_message="Unable to connect"
                )
            )
        ]
        with pytest.raises(SystemExit) as exception:
            results_uploader.upload_results()

        environment.log.assert_has_calls(expected_log_calls)
        assert (
            exception.type == SystemExit
        ), f"Expected SystemExit exception, but got {exception.type} instead."
        assert (
            exception.value.code == exit_code
        ), f"Expected exit code {exit_code}, but got {exception.value.code} instead."

    @pytest.mark.results_uploader
    @pytest.mark.parametrize(
        "failing_function",
        TEST_UPLOAD_RESULTS_FLOW_TEST_DATA,
        ids=TEST_UPLOAD_RESULTS_FLOW_IDS,
    )
    def test_upload_results_flow(
        self, failing_function, result_uploader_data_provider, mocker
    ):
        """The purpose of those tests is to check that proper message would be printed and trcli tool
        will terminate with proper code when one of the functions in the flow fails."""
        (
            environment,
            api_request_handler,
            results_uploader,
        ) = result_uploader_data_provider
        project_id = 10
        exit_code = 1
        environment.run_id = None
        get_project_id_mocker(
            results_uploader=results_uploader,
            project_id=project_id,
            error_message="",
            failing=True,
        )
        upload_results_inner_functions_mocker(
            results_uploader=results_uploader,
            mocker=mocker,
            failing_functions=[failing_function],
        )

        with pytest.raises(SystemExit) as exception:
            results_uploader.upload_results()

        assert (
            exception.type == SystemExit
        ), f"Expected SystemExit exception, but got {exception.type} instead."
        assert (
            exception.value.code == exit_code
        ), f"Expected exit code {exit_code}, but got {exception.value.code} instead."

    @pytest.mark.parametrize(
        "run_id", [None, 10], ids=["No run ID provided", "Run ID provided"]
    )
    @pytest.mark.results_uploader
    def test_upload_results_successful(
        self, run_id, result_uploader_data_provider, mocker
    ):
        """The purpose of this test is to check if during successful run of upload_results proper messages
        would be printed."""
        (
            environment,
            api_request_handler,
            results_uploader,
        ) = result_uploader_data_provider
        project_id = 10
        environment.run_id = run_id
        get_project_id_mocker(
            results_uploader=results_uploader,
            project_id=project_id,
            error_message="",
            failing=True,
        )
        upload_results_inner_functions_mocker(
            results_uploader=results_uploader, mocker=mocker, failing_functions=[]
        )
        expected_log_calls = []
        if not run_id:
            expected_log_calls.extend(
                [
                    mocker.call("Creating test run. ", new_line=False),
                    mocker.call("Done."),
                ]
            )
        expected_log_calls.extend(
            [mocker.call("Closing test run. ", new_line=False), mocker.call("Done.")]
        )
        results_uploader.upload_results()

        environment.log.assert_has_calls(expected_log_calls)

    @pytest.mark.results_uploader
    def test_get_suite_id_returns_valid_id(self, result_uploader_data_provider):
        """The purpose of this test is to check that __get_suite_id function will
        return suite_id if it exists in TestRail"""
        (
            environment,
            api_request_handler,
            results_uploader,
        ) = result_uploader_data_provider
        suite_id = 10
        result_code = 1
        project_id = 1
        results_uploader.api_request_handler.suites_data_from_provider.suite_id = (
            suite_id
        )
        results_uploader.api_request_handler.check_suite_id.return_value = True
        (
            result_suite_id,
            result_return_code,
        ) = results_uploader._ResultsUploader__get_suite_id(
            project_id=project_id, suite_mode=SuiteModes.single_suite
        )

        assert (
            result_suite_id == suite_id
        ), f"Expected suite_id: {suite_id} but got {result_suite_id} instead."
        assert (
            result_return_code == result_code
        ), f"Expected suite_id: {result_code} but got {result_return_code} instead."

    @pytest.mark.results_uploader
    @pytest.mark.parametrize(
        "user_response, expected_suite_id, expected_result_code, expected_message, suite_add_error",
        TEST_GET_SUITE_ID_PROMPTS_USER_TEST_DATA,
        ids=TEST_GET_SUITE_ID_PROMPTS_USER_IDS,
    )
    def test_get_suite_id_multiple_suites_mode(
        self,
        user_response,
        expected_suite_id,
        expected_result_code,
        expected_message,
        suite_add_error,
        result_uploader_data_provider,
        mocker,
    ):
        """The purpose of this test is to check that user will be prompted to add suite is one is missing
        in TestRail. Depending on user response either information about addition of missing suite or error message
        should be printed."""
        (
            environment,
            api_request_handler,
            results_uploader,
        ) = result_uploader_data_provider
        project_id = 1
        suite_name = "Fake suite name"
        suite_mode = SuiteModes.multiple_suites
        if not suite_add_error:
            results_uploader.api_request_handler.add_suite.return_value = (
                [
                    {
                        "suite_id": expected_suite_id,
                        "name": suite_name,
                    }
                ],
                "",
            )
        else:
            results_uploader.api_request_handler.add_suite.return_value = (
                [{"suite_id": expected_suite_id, "name": suite_name}],
                FAULT_MAPPING["error_while_adding_suite"].format(
                    error_message="Failed to add suite."
                ),
            )
        results_uploader.api_request_handler.suites_data_from_provider.suite_id = None
        results_uploader.api_request_handler.suites_data_from_provider.name = suite_name
        environment.get_prompt_response_for_auto_creation.return_value = user_response
        result_suite_id, result_code = results_uploader._ResultsUploader__get_suite_id(
            project_id, suite_mode
        )
        expected_log_calls = [mocker.call(expected_message)]
        if suite_add_error:
            expected_log_calls.append(
                mocker.call(
                    FAULT_MAPPING["error_while_adding_suite"].format(
                        error_message="Failed to add suite."
                    )
                )
            )

        assert (
            expected_suite_id == result_suite_id
        ), f"Expected suite_id: {expected_suite_id} but got {result_suite_id} instead."
        assert (
            expected_result_code == result_code
        ), f"Expected suite_id: {expected_result_code} but got {result_code} instead."
        environment.get_prompt_response_for_auto_creation.assert_called_with(
            PROMPT_MESSAGES["create_new_suite"].format(
                suite_name=suite_name,
                project_name=environment.project,
            )
        )
        if user_response:
            results_uploader.api_request_handler.add_suite.assert_called_with(
                project_id=project_id
            )
        environment.log.assert_has_calls(expected_log_calls)

    @pytest.mark.results_uploader
    @pytest.mark.parametrize(
        "suite_ids, error_message, expected_suite_id, expected_result_code",
        [([10], "", 10, 1), ([], "Could not get suites", -1, -1)],
        ids=["get_suite_ids succeeds", "get_suite_ids fails"],
    )
    def test_get_suite_id_single_suite_mode(
        self,
        suite_ids,
        error_message,
        expected_suite_id,
        expected_result_code,
        result_uploader_data_provider,
        mocker,
    ):
        """The purpose of this test is to check flow of get_suite_id_log_error function for single
        suite mode."""
        (
            environment,
            api_request_handler,
            results_uploader,
        ) = result_uploader_data_provider
        project_id = 1
        suite_mode = SuiteModes.single_suite
        results_uploader.api_request_handler.suites_data_from_provider.suite_id = None
        results_uploader.api_request_handler.get_suite_ids.return_value = (
            suite_ids,
            error_message,
        )
        if error_message:
            expected_log_calls = [mocker.call(error_message)]
        result_suite_id, result_code = results_uploader._ResultsUploader__get_suite_id(
            project_id, suite_mode
        )

        assert (
            result_suite_id == expected_suite_id
        ), f"Expected suite id: {expected_suite_id} but got {result_suite_id} instead."
        assert (
            result_code == expected_result_code
        ), f"Expected result code: {expected_result_code} but got {result_code} instead."
        if error_message:
            environment.log.assert_has_calls(expected_log_calls)

    @pytest.mark.results_uploader
    @pytest.mark.parametrize(
        "get_suite_ids_result, expected_suite_id, expected_result_code, expected_error_message",
        TEST_GET_SUITE_ID_SINGLE_SUITE_MODE_BASELINES_TEST_DATA,
        ids=TEST_GET_SUITE_ID_SINGLE_SUITE_MODE_BASELINES_IDS,
    )
    def test_get_suite_id_single_suite_mode_baselines(
        self,
        get_suite_ids_result,
        expected_suite_id,
        expected_result_code,
        expected_error_message,
        result_uploader_data_provider,
        mocker,
    ):
        """The purpose of this test is to check flow of get_suite_id_log_error function for single
        suite with baselines mode."""
        (
            environment,
            api_request_handler,
            results_uploader,
        ) = result_uploader_data_provider
        project_id = 1
        suite_mode = SuiteModes.single_suite_baselines
        results_uploader.api_request_handler.suites_data_from_provider.suite_id = None
        results_uploader.api_request_handler.get_suite_ids.return_value = (
            get_suite_ids_result
        )
        expected_log_calls = []
        if expected_error_message:
            expected_log_calls = [mocker.call(expected_error_message)]
        result_suite_id, result_code = results_uploader._ResultsUploader__get_suite_id(
            project_id, suite_mode
        )

        assert (
            result_suite_id == expected_suite_id
        ), f"Expected suite id: {expected_suite_id} but got {result_suite_id} instead."
        assert (
            result_code == expected_result_code
        ), f"Expected result code: {expected_result_code} but got {result_code} instead."
        if expected_error_message:
            environment.log.assert_has_calls(expected_log_calls)

    @pytest.mark.results_uploader
    def test_get_suite_id_unknown_suite_mode(
        self, result_uploader_data_provider, mocker
    ):
        """The purpose of this test is to check that get_suite_id will return -1 and print
        proper message when unknown suite mode will be returned during execution."""
        (
            environment,
            api_request_handler,
            results_uploader,
        ) = result_uploader_data_provider
        project_id = 1
        suite_mode = 4
        expected_result_code = -1
        expected_suite_id = -1
        results_uploader.api_request_handler.suites_data_from_provider.suite_id = None
        expected_log_calls = [
            mocker.call(
                FAULT_MAPPING["unknown_suite_mode"].format(suite_mode=suite_mode)
            )
        ]
        result_suite_id, result_code = results_uploader._ResultsUploader__get_suite_id(
            project_id, suite_mode
        )

        assert (
            result_suite_id == expected_suite_id
        ), f"Expected suite id: {expected_suite_id} but got {result_suite_id} instead."
        assert (
            result_code == expected_result_code
        ), f"Expected result code: {expected_result_code} but got {result_code} instead."
        environment.log.assert_has_calls(expected_log_calls)

    @pytest.mark.results_uploader
    def test_check_suite_id_returns_id(self, result_uploader_data_provider):
        """The purpose of this test is to check that __check_suite_id function will return suite ID,
        when suite ID exists under specified project."""
        (
            environment,
            api_request_handler,
            results_uploader,
        ) = result_uploader_data_provider
        expected_result_code = 1
        suite_id = 1
        project_id = 2
        results_uploader.api_request_handler.check_suite_id.return_value = True

        (
            result_suite_id,
            result_code,
        ) = results_uploader._ResultsUploader__check_suite_id(
            suite_id=suite_id, project_id=project_id
        )

        assert (
            result_suite_id == suite_id
        ), f"Expected to get {suite_id} as suite ID, but got {result_suite_id} instead."
        assert (
            result_code == expected_result_code
        ), f"Expected to get {result_code} as result code, but got {expected_result_code} instead."

    @pytest.mark.results_uploader
    def test_check_suite_id_prints_error_message(
        self, result_uploader_data_provider, mocker
    ):
        """The purpose of this test is to check that proper message would be printed to the user
        and program will quit when suite ID is not present in TestRail."""
        (
            environment,
            api_request_handler,
            results_uploader,
        ) = result_uploader_data_provider
        suite_id = 1
        expected_result_code = -1
        project_id = 2
        results_uploader.api_request_handler.check_suite_id.return_value = False

        (
            result_suite_id,
            result_code,
        ) = results_uploader._ResultsUploader__check_suite_id(
            suite_id=suite_id, project_id=project_id
        )
        expected_log_calls = [
            mocker.call(FAULT_MAPPING["missing_suite"].format(suite_id=suite_id))
        ]

        environment.log.assert_has_calls(expected_log_calls)
        assert (
            result_code == expected_result_code
        ), f"Expected to get {expected_result_code} as result code, but got {result_code} instead."
        assert (
            result_suite_id == suite_id
        ), f"Expected to get {suite_id} as suite id, but got {result_suite_id} instead."

    @pytest.mark.results_uploader
    def test_add_missing_sections_no_missing_sections(
        self, result_uploader_data_provider
    ):
        """The purpose of this test is to check that __add_missing_sections will return empty list
        and proper return code when there are no missing sections."""
        (
            environment,
            api_request_handler,
            results_uploader,
        ) = result_uploader_data_provider
        project_id = 1
        return_code = 1
        missing_sections = []
        results_uploader.api_request_handler.check_missing_section_id.return_value = (
            missing_sections,
            "",
        )
        result = results_uploader._ResultsUploader__add_missing_sections(project_id)

        assert result == (
            missing_sections,
            return_code,
        ), f"Expected to get {missing_sections, return_code} as a result but got {result} instead."

    @pytest.mark.results_uploader
    @pytest.mark.parametrize(
        "user_response, missing_sections, expected_add_sections_error, expected_added_sections,"
        "expected_message, expected_result_code",
        TEST_ADD_MISSING_SECTIONS_PROMPTS_USER_TEST_DATA,
        ids=TEST_ADD_MISSING_SECTIONS_PROMPTS_USER_IDS,
    )
    def test_add_missing_sections_prompts_user(
        self,
        user_response,
        missing_sections,
        expected_add_sections_error,
        expected_added_sections,
        expected_message,
        expected_result_code,
        result_uploader_data_provider,
        mocker,
    ):
        """The purpose of this test is to check that __add_missing_sections prompts user
        for adding missing sections."""
        (
            environment,
            api_request_handler,
            results_uploader,
        ) = result_uploader_data_provider
        project_id = 1
        results_uploader.api_request_handler.check_missing_section_id.return_value = (
            missing_sections,
            "",
        )
        results_uploader.environment.get_prompt_response_for_auto_creation.return_value = (
            user_response
        )
        results_uploader.api_request_handler.add_section.return_value = (
            expected_added_sections,
            expected_add_sections_error,
        )

        (
            result_added_sections,
            result_code,
        ) = results_uploader._ResultsUploader__add_missing_sections(project_id)
        expected_log_calls = [mocker.call(expected_message)]
        if expected_add_sections_error:
            expected_log_calls.append(mocker.call(expected_add_sections_error))

        assert (
            result_code == expected_result_code
        ), f"Expected result_code {expected_result_code} but got {result_code} instead."
        assert (
            result_added_sections == expected_added_sections
        ), f"Expected sections to be added: {expected_added_sections} but got {result_added_sections} instead."
        environment.log.assert_has_calls(expected_log_calls)
        environment.get_prompt_response_for_auto_creation.assert_called_with(
            PROMPT_MESSAGES["create_missing_sections"].format(
                project_name=environment.project
            )
        )

    @pytest.mark.results_uploader
    def test_add_missing_sections_error_checking(
        self, result_uploader_data_provider, mocker
    ):
        """The purpose of this test is to check that __add_missing_sections will return empty list
        and -1 as a result code when check_missing_section_id will fail. Proper message will be printed."""
        (
            environment,
            api_request_handler,
            results_uploader,
        ) = result_uploader_data_provider
        project_id = 1
        return_code = -1
        missing_sections = []
        error_message = "Connection Error."
        results_uploader.api_request_handler.check_missing_section_id.return_value = (
            [],
            error_message,
        )
        result = results_uploader._ResultsUploader__add_missing_sections(project_id)
        expected_log_calls = [
            mocker.call(
                FAULT_MAPPING["error_checking_missing_item"].format(
                    missing_item="missing sections", error_message=error_message
                )
            )
        ]

        environment.log.assert_has_calls(expected_log_calls)
        assert result == (
            missing_sections,
            return_code,
        ), f"Expected to get {missing_sections, return_code} as a result but got {result} instead."

    @pytest.mark.results_uploader
    def test_add_missing_test_cases_no_missing_test_cases(
        self, result_uploader_data_provider
    ):
        """The purpose of this test is to check that __add_missing_test_cases will
        return empty list and proper return code when there are no missing tests cases."""
        (
            environment,
            api_request_handler,
            results_uploader,
        ) = result_uploader_data_provider
        project_id = 1
        result_code = 1
        missing_test_cases = []
        results_uploader.api_request_handler.check_missing_test_cases_ids.return_value = (
            missing_test_cases,
            "",
        )
        result = results_uploader._ResultsUploader__add_missing_test_cases(project_id)

        assert result == (
            missing_test_cases,
            result_code,
        ), f"Expected to get {(missing_test_cases, result_code)} as a result but got {result} instead."

    @pytest.mark.results_uploader
    @pytest.mark.parametrize(
        "user_response, missing_test_cases, expected_add_test_cases_error, expected_added_test_cases, "
        "expected_message, expected_result_code",
        TEST_ADD_MISSING_TEST_CASES_PROMPTS_USER_TEST_DATA,
        ids=TEST_ADD_MISSING_TEST_CATAS_PROMPTS_USER_IDS,
    )
    def test_add_missing_test_cases_prompts_user(
        self,
        user_response,
        missing_test_cases,
        expected_add_test_cases_error,
        expected_added_test_cases,
        expected_message,
        expected_result_code,
        result_uploader_data_provider,
        mocker,
    ):
        """The purpose of this test is to check that __add_missing_test_cases function will
        prompt the user for adding missing test cases."""
        (
            environment,
            api_request_handler,
            results_uploader,
        ) = result_uploader_data_provider
        project_id = 1
        results_uploader.api_request_handler.check_missing_test_cases_ids.return_value = (
            missing_test_cases,
            expected_message,
        )
        results_uploader.environment.get_prompt_response_for_auto_creation.return_value = (
            user_response
        )
        results_uploader.api_request_handler.add_case.return_value = (
            expected_added_test_cases,
            expected_add_test_cases_error,
        )

        (
            result_added_test_cases,
            result_code,
        ) = results_uploader._ResultsUploader__add_missing_test_cases(project_id)
        expected_log_calls = [mocker.call(expected_message)]
        if expected_add_test_cases_error:
            expected_log_calls.append(mocker.call(expected_add_test_cases_error))

        assert (
            result_code == expected_result_code
        ), f"Expected result_code {expected_result_code} but got {result_code} instead."
        assert (
            result_added_test_cases == expected_added_test_cases
        ), f"Expected test cases to be added: {expected_added_test_cases} but got {result_added_test_cases} instead."
        environment.log.assert_has_calls(expected_log_calls)
        environment.get_prompt_response_for_auto_creation.assert_called_with(
            PROMPT_MESSAGES["create_missing_test_cases"].format(
                project_name=environment.project
            )
        )

    @pytest.mark.results_uploader
    def test_add_missing_test_cases_error_checking(
        self, result_uploader_data_provider, mocker
    ):
        """The purpose of this test is to check that __add_missing_test_cases will return empty list
        and -1 as result code when check_missing_test_cases_ids will fail. Proper message will be printed."""
        (
            environment,
            api_request_handler,
            results_uploader,
        ) = result_uploader_data_provider
        project_id = 1
        return_code = -1
        missing_test_cases = []
        error_message = "Connection Error."
        results_uploader.api_request_handler.check_missing_test_cases_ids.return_value = (
            [],
            error_message,
        )
        result = results_uploader._ResultsUploader__add_missing_test_cases(project_id)
        expected_log_calls = [
            mocker.call(
                FAULT_MAPPING["error_checking_missing_item"].format(
                    missing_item="missing test cases", error_message=error_message
                )
            )
        ]

        environment.log.assert_has_calls(expected_log_calls)
        assert result == (
            missing_test_cases,
            return_code,
        ), f"Expected to get {missing_test_cases, return_code} as a result but got {result} instead."

    @pytest.mark.results_uploader
    @pytest.mark.parametrize(
        "timeout", [40, None], ids=["with_timeout", "without_timeout"]
    )
    def test_instantiate_api_client(
        self, timeout, result_uploader_data_provider, mocker
    ):
        """The purpose of this test is to check that APIClient was instantiated properly and credential fields
        were set es expected."""
        (_, api_request_handler, _) = result_uploader_data_provider
        junit_file_parser = mocker.patch.object(JunitParser, "parse_file")
        environment = Environment()
        environment.host = "https://fake_host.com"
        environment.username = "usermane@host.com"
        environment.password = "test_password"
        environment.key = "test_api_key"
        if timeout:
            environment.timeout = timeout
        timeout_expected_result = 30 if not timeout else timeout
        result_uploader = ResultsUploader(
            environment=environment, result_file_parser=junit_file_parser
        )

        api_client = result_uploader._ResultsUploader__instantiate_api_client()

        assert (
            api_client.username == environment.username
        ), f"Expected username to be set to: {environment.username}, but got: {api_client.username} instead."
        assert (
            api_client.password == environment.password
        ), f"Expected password  to be set to: {environment.password}, but got: {api_client.password} instead."
        assert (
            api_client.api_key == environment.key
        ), f"Expected api_key to be set to: {environment.key}, but got: {api_client.api_key} instead."
        assert (
            api_client.timeout == timeout_expected_result
        ), f"Expected timeout to be set to: {timeout_expected_result}, but got: {api_client.timeout} instead."
