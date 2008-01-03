<?php
/**
 *  Orbited PHP Chat Client
 *  
 *  Copyright (c) 2007 Michael Zaic <mzaic@cafemom.com>, CafeMom.com
 *  http://www.cafemom.com
 *  http://www.orbited.org
 * 
 *  Licensed under The MIT License: <http://www.opensource.org/licenses/mit-license.php>
 */

require_once('php-orbited.php');
$orbited = new OrbitedClient('localhost', 9000);

function user_keys()
{
    $users = file('users.txt');
    $list = array();
    foreach($users as $user) {
        $user = explode(',', trim($user));
        $list[] = $user[0].', '.$user[1].', /phpchat';
    }
    return $list;
}

$action  = isset($_GET['action'])  ? $_GET['action']  : null; 
$msg     = isset($_GET['msg'])     ? $_GET['msg']     : null; 
$user    = isset($_GET['user'])    ? $_GET['user']    : null; 
$id      = isset($_GET['id'])      ? $_GET['id']      : null; 
$session = isset($_GET['session']) ? $_GET['session'] : 0; 

if ( $action == 'join' && $user ) {
    // Add user
    $user_session = $user.','.$session;
    $users = file('users.txt', FILE_IGNORE_NEW_LINES);
    if(!in_array($user_session, $users)){
        $handle = fopen('users.txt', 'a');
        fwrite($handle, $user_session."\n");
        fclose($handle);
    }
    // Notify "room" 
    $orbited->event(user_keys(), '**** '.$user.' has joined ****');
    echo 'ok.';

}

elseif ( $action == 'msg' && $msg && $user ) { 
    // Send message to room
    $orbited->event(user_keys(), ''.$user.': '.$msg);
    echo 'ok.';
}

//// removing leaving from this demo, to align it with cherrypy/rails/etc.
//// versions --jacob
//
// elseif ( $action == 'leave' && $user ) {
//     $user_session = $user.','.$session;
//     $users = file('users.txt', FILE_IGNORE_NEW_LINES);
//     $new_users = array();
//     $in_room = false;
//     foreach($users as $line){
//         if(trim($line) != $user_session) {
//             $new_users[] = $line;
//         }
//         else {
//             $in_room = true;
//         }
//     }
//     if($in_room) {
//         $handle = fopen('users.txt', 'w');
//         foreach($new_users as $line) {
//             fwrite($handle, $line."\n");
//         }
//         fclose($handle);
//     }
//     
//     $orbited->event(user_keys(), '**** '.$user.' has left the room ****');
//     echo 'ok.';
// }
?>
