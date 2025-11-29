from jnius import autoclass

def ensure_record_permission():
    try:
        # Nếu đang chạy trên Android, dùng Pyjnius để kiểm tra quyền
        from jnius import autoclass

        PythonActivity = autoclass('org.beeware.android.MainActivity')
        activity = PythonActivity.singletonThis

        ContextCompat = autoclass('androidx.core.content.ContextCompat')
        Manifest = autoclass('android.Manifest')
        PackageManager = autoclass('android.content.pm.PackageManager')

        permission = Manifest.permission.RECORD_AUDIO
        granted = ContextCompat.checkSelfPermission(activity, permission)

        return granted == PackageManager.PERMISSION_GRANTED

    except ImportError:

        return True