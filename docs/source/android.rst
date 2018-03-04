piecash on android
==================

piecash can successfully run on android which opens interesting opportunities!

Installing termux
-----------------

First, you have to install Termux from the Play Store.

You start Termux and:

 1. edit your .bash_profile with::

        export TZ=$(getprop persist.sys.timezone)
        export SHELL=$(which bash)

 2. add the folder ~/storage with access to your android folders (also accessible via USB sync)::

        termux-setup-storage


Installing python and piecash
-----------------------------

You start Termux on your android and then:

 1. Install python and pipenv::

        pkg install python
        pip install pipenv


 2. Install piecash for your project::

        mkdir my-project
        cd my-project
        pipenv install piecash


 3. Test piecash::

        pipenv shell
        python
        >>> import piecash


Use SSH with your android
-------------------------

You can ssh easily in your android thanks to Termux.
For this, on Termux on your android:

 1. install openssh::

        pkg install openssh

 2. add your public key (id_rsa.pub) in the file `.ssh/authorized_keys` on Termux

 3. run the sshd server::

        sshd

On your machine (laptop, ...):

 1. configure your machine to access your android device::

        Host android
           HostName 192.168.1.4  # <== put the IP address of your android
           User termux
           Port 8022

 2. log in your android from your machine::

        ssh android


Use the USB Debugging with your android
---------------------------------------

To be investigated...::

    # on laptop
    adb forward tcp:8022 tcp:8022 && ssh localhost -p 8022

    # on android
    # On Android 4.2 and higher, the Developer options screen is hidden by default. To make it visible, go to Settings > About phone and tap Build number seven times. Return to the previous screen to find Developer options at the bottom.
    change USB Configuration to "charge only" or "PTP"

    # downloading https://developer.android.com/studio/run/win-usb.html
    # Click here to download the Google USB Driver ZIP file (Z
    # install legacy hardware (in device manager)
    # choose the folder of the zip drive and choose ADB interface


References
----------

- https://glow.li/technology/2015/11/06/run-an-ssh-server-on-your-android-with-termux/
- https://termux.com/storage.html
- https://developer.android.com/studio/releases/platform-tools.html
- https://glow.li/technology/2016/9/20/access-termux-via-usb/
- https://github.com/termux/termux-packages/issues/352

