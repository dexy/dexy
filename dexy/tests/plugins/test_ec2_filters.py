from dexy.doc import Doc
from dexy.plugins.ec2_filters import EC2Launch
from dexy.tests.utils import wrap
from mock import Mock
from mock import patch
from nose.exc import SkipTest
import dexy.exceptions

try:
    import boto
except ImportError:
    raise SkipTest

def test_ec2_launch_setup_child_docs():
    with wrap() as wrapper:
        with open("hello.txt", "w") as f:
            f.write("hello")

        doc = Doc("hello.txt|jinja")
        assert doc.state == 'new'
        EC2Launch("test", doc, wrapper=wrapper)
        assert doc.state == 'new'

def test_ec2_launch_invalid_shutdown_behavior():
    try:
        task = EC2Launch("test", shutdown_behavior="shutdown")
        task.shutdown_behavior()
        assert False, "should raise UserFeedback"
    except dexy.exceptions.UserFeedback as e:
        assert "shutdown behavior 'shutdown' not available" in e.message

@patch('boto.connect_ec2')
def test_ec2_launch_shutting_down(mock_connect_ec2):
    mock_ec2_instance = Mock()
    mock_connect_ec2.return_value.run_instances.return_value.instances = [mock_ec2_instance]
    mock_ec2_instance.state = 'shutting-down'

    with wrap() as wrapper:
        doc = Doc("hello.txt|jinja", contents="hello", wrapper=wrapper)

        task = EC2Launch("test",
                doc,
                wrapper=wrapper,
                ec2_keypair="mykeypair"
                )

        try:
            wrapper.run_docs(task)
            assert False, "should raise UserFeedback"
        except dexy.exceptions.UserFeedback as e:
            assert "Oops! instance shutting down already" in e.message

@patch('boto.connect_ec2')
def test_ec2_launch_terminated(mock_connect_ec2):
    mock_ec2_instance = Mock()
    mock_connect_ec2.return_value.run_instances.return_value.instances = [mock_ec2_instance]
    mock_ec2_instance.state = 'terminated'

    with wrap() as wrapper:
        doc = Doc("hello.txt|jinja", contents="hello",wrapper=wrapper)

        task = EC2Launch("test",
                doc,
                wrapper=wrapper,
                ec2_keypair="mykeypair"
                )

        try:
            wrapper.run_docs(task)
            assert False, "should raise UserFeedback"
        except dexy.exceptions.UserFeedback as e:
            assert "Oops! instance terminated already" in e.message

@patch('boto.connect_ec2')
def test_ec2_launch(mock_connect_ec2):
    mock_ec2_instance = Mock()
    mock_connect_ec2.return_value.run_instances.return_value.instances = [mock_ec2_instance]
    mock_ec2_instance.state_count = 0

    def side_effect():
        mock_ec2_instance.state_count += 1
        if mock_ec2_instance.state_count < 2:
            mock_ec2_instance.state = 'pending'
        else:
            mock_ec2_instance.state = 'running'

    mock_ec2_instance.update = side_effect

    with wrap() as wrapper:
        doc = Doc("hello.txt|jinja", contents="hello", wrapper=wrapper)

        task = EC2Launch("test",
                doc,
                wrapper=wrapper,
                ami="abc123",
                ec2_keypair="mykeypair",
                instance_type="xxxlarge",
                shutdown_behavior="stop"
                )

        task.set_log()

        assert task.ami() == "abc123"
        assert task.instance_type() == "xxxlarge"
        assert task.shutdown_behavior() == "stop"
        assert task.ec2_keypair_name() == 'mykeypair'
        assert task.ec2_keypair_filepath().endswith("mykeypair.pem")

        wrapper.run_docs(task)

        mock_ec2_instance.terminate.assert_called_with()
