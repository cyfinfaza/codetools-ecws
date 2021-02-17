function requestnoti() {
    Notification.requestPermission(function(status) {
        console.log('Notification permission status:', status);
    });
}
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('serviceworker.js').then(function(reg) {
            console.log('Service Worker Registered!', reg);

            reg.pushManager.getSubscription().then(function(sub) {
                if (sub === null) {
                    // Update UI to ask user to register for Push
                    console.log('Not subscribed to push service!');
                } else {
                    // We have a subscription, update the database
                    console.log('Subscription object: ', sub);
                }
            });
        })
        .catch(function(err) {
            console.log('Service Worker registration failed: ', err);
        });
}

function testNotification() {
    var options = {
        body: 'This is a test notification',
        icon: 'images/cy2.png',
        vibrate: [100, 50, 100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: '2'
        },
        actions: [{
                action: 'explore',
                title: 'Explore this new world',
                icon: 'images/sc1.jpg'
            },
            {
                action: 'close',
                title: 'Close',
                icon: 'images/sc2.jpg'
            },
        ]
    };
    console.log('sending test notif')
        // self.registration.showNotification('Hello world!', options)
        // Notification.showNotification('Hello world!', options)
        // navigator.serviceWorker.getRegistration().then(function(reg) {
        //     reg.showNotification('Hello world!', options);
        // });
        // navigator.serviceWorker.ready.then(registration => {
        //     registration.showNotification('Vibration Sample', {
        //         body: 'Buzz! Buzz!',
        //         tag: 'vibration-sample'
        //     });
        // });
        // new Notification('Hello world!', options)
    var img = '/to-do-notifications/img/icon-128.png';
    var text = 'HEY! Your task is now overdue.';
    var notification = new Notification('To do list', { body: text, icon: img });
}

function subscribeUser() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.ready.then(function(reg) {
            console.log('CURR SUB INFO: ', JSON.stringify(reg.pushManager.getSubscription()));
            reg.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: 'BPdGHyMpEwouUwnrZK2i3ldPR7XnVX1fbOnHQS8u8oG64RtnVvC7pvDRSdED0QNZ0VH46qNAEHasuej1-X4R_Mw'
            }).then(function(sub) {
                console.log('SUB INFO: ', JSON.stringify(sub));
                document.getElementById('readout').innerHTML = JSON.stringify(sub)
            }).catch(function(e) {
                if (Notification.permission === 'denied') {
                    console.warn('Permission for notifications was denied');
                } else {
                    console.error('Unable to subscribe to push', e);
                }
            });
        })
    }
}
testNotification()
subscribeUser()
requestnoti()