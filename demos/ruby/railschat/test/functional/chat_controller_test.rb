require File.dirname(__FILE__) + '/../test_helper'
require 'chat_controller'

# Re-raise errors caught by the controller.
class ChatController; def rescue_action(e) raise e end; end

class ChatControllerTest < Test::Unit::TestCase
  def setup
    @controller = ChatController.new
    @request    = ActionController::TestRequest.new
    @response   = ActionController::TestResponse.new
  end

  # Replace this with your real tests.
  def test_truth
    assert true
  end
end
