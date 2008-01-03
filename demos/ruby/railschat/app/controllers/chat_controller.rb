def user_keys
  list = []
  for user in $users do
    list = list + [user[0] + ", " + user[1].to_s + ", /railschat",]
  end
  return list
end

class ChatController < ApplicationController
  
  def index
  end
  
  def join
    user = params[:user]
    session = params[:session] || 0
    ie_nocache = params[:ie_nocache]
    
    if not $users.member?([user, session])
      $users = $users + [[user, session]]
      $orbit.event(user_keys(), '*' + user + ' joined*')
    end
    render :text => "ok."
  end
  
  def msg
    session = params[:session] || 0
    ie_nocache = params[:ie_nocache] || nil
    
    $orbit.event(user_keys(), '' + params[:user] + ': ' + params[:msg])
    render :text => "ok."
  end
end