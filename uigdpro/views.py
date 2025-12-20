import io
import json
import os
import re
import base64
import logging
from pathlib import Path
from uuid import UUID
import requests
from PIL import Image
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.db.models import Q
from django.http import (
    HttpResponse,
    JsonResponse,
    Http404,
    FileResponse,
)
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .forms import GenerateForm
from .models import GithubRun

logger = logging.getLogger(__name__)


def save_png(file_input, uuid_str: str, domain: str, name: str) -> str | None:
    """
    Save PNG file (from UploadedFile or base64 string) to disk.
    Returns JSON string with url/uuid/file on success, None on failure.
    """
    allowed_names = {"icon.png", "logo.png"}
    if name not in allowed_names:
        logger.warning(f"Disallowed PNG name: {name}")
        return None

    try:
        UUID(uuid_str)
    except ValueError:
        logger.error(f"Invalid UUID: {uuid_str}")
        return None

    # Limit image size to prevent DoS
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB

    image_bytes = None
    if isinstance(file_input, str):
        if not file_input.startswith("data:image/"):
            logger.warning("Base64 input missing 'data:image/' prefix")
            return None
        try:
            header, b64_part = file_input.split(";base64,", 1)
            image_bytes = base64.b64decode(b64_part)
            if len(image_bytes) > MAX_IMAGE_SIZE:
                logger.warning("Base64 image too large")
                return None
        except (ValueError, base64.binascii.Error) as e:
            logger.error(f"Base64 decode error: {e}")
            return None
    elif hasattr(file_input, 'chunks'):
        try:
            chunks = []
            total = 0
            for chunk in file_input.chunks():
                total += len(chunk)
                if total > MAX_IMAGE_SIZE:
                    logger.warning("Uploaded image too large")
                    return None
                chunks.append(chunk)
            image_bytes = b''.join(chunks)
        except Exception as e:
            logger.error(f"File read error: {e}")
            return None
    else:
        logger.error("Unsupported file_input type")
        return None

    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        output_buffer = io.BytesIO()
        img.save(output_buffer, format="PNG")
        final_bytes = output_buffer.getvalue()
    except Exception as e:
        logger.error(f"Image processing failed: {e}")
        return None

    save_dir = Path(settings.BASE_DIR) / "png" / uuid_str
    save_dir.mkdir(parents=True, exist_ok=True)
    file_path = save_dir / name

    try:
        with open(file_path, "wb") as f:
            f.write(final_bytes)
    except OSError as e:
        logger.error(f"File write error: {e}")
        return None

    result = {
        "url": domain.rstrip("/"),
        "uuid": uuid_str,
        "file": name,
    }
    return json.dumps(result)


def create_github_run(myuuid: str, filename: str, direction: str, platform: str):
    new_run = GithubRun(
        uuid=myuuid,
        filename=filename,
        direction=direction,
        platform=platform,
        status="InProgress"
    )
    new_run.save()


@csrf_exempt
def generator_view(request):
    if request.method == 'POST':
        form = GenerateForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, 'generator.html', {'form': form, 'errors': form.errors})

        # Extract cleaned data
        cd = form.cleaned_data
        platform = cd['platform']
        version = cd['version']
        delayFix = cd['delayFix']
        cycleMonitor = cd['cycleMonitor']
        xOffline = cd['xOffline']
        hidecm = cd['hidecm']
        removeNewVersionNotif = cd['removeNewVersionNotif']
        hidePassword = cd['hidePassword']
        hideMenuBar = cd['hideMenuBar']
        removeTopNotice = cd['removeTopNotice']
        password_security_length = cd['password_security_length']
        server = cd['serverIP'] or 'rs-ny.rustdesk.com'
        key = cd['key'] or 'OeVuKk5nlHiXp+APNn0Y3pC1Iwpwn44JGqrQCsWqmBw='
        apiServer = cd['apiServer'] or f"{server}:21114"
        urlLink = cd['urlLink'] or "https://rustdesk.com"
        downloadLink = cd['downloadLink'] or "https://rustdesk.com/download"
        direction = cd['direction']
        installation = cd['installation']
        settings_flag = cd['settings']
        appname = cd['appname']
        filename = cd['exename']
        compname = (cd['compname'] or "Purslane Ltd").replace("&", "\\&")
        permPass = cd['permanentPassword']
        theme = cd['theme']
        themeDorO = cd['themeDorO']
        passApproveMode = cd['passApproveMode']
        denyLan = cd['denyLan']
        enableDirectIP = cd['enableDirectIP']
        autoClose = cd['autoClose']
        permissionsDorO = cd['permissionsDorO']
        permissionsType = cd['permissionsType']

        # Boolean flags
        bool_flags = {
            'enableKeyboard': cd['enableKeyboard'],
            'enableClipboard': cd['enableClipboard'],
            'enableFileTransfer': cd['enableFileTransfer'],
            'enableAudio': cd['enableAudio'],
            'enableTCP': cd['enableTCP'],
            'enableRemoteRestart': cd['enableRemoteRestart'],
            'enableRecording': cd['enableRecording'],
            'enableBlockingInput': cd['enableBlockingInput'],
            'enableRemoteModi': cd['enableRemoteModi'],
            'removeWallpaper': cd['removeWallpaper'],
            'enablePrinter': cd['enablePrinter'],
            'enableCamera': cd['enableCamera'],
            'enableTerminal': cd['enableTerminal'],
        }

        # Sanitize filename
        if filename and all(c.isascii() for c in filename):
            filename = re.sub(r'[^\w\s\-]', '_', filename).strip().replace(' ', '_')
            if not filename:
                filename = "rustdesk"
        else:
            filename = "rustdesk"

        # Sanitize appname
        if not appname or not all(c.isascii() for c in appname):
            appname = "rustdesk"

        myuuid = str(UUID(int=0))  # placeholder; will replace
        myuuid = str(UUID(bytes=os.urandom(16)))  # better randomness
        protocol = getattr(settings, 'PROTOCOL', 'https')
        host = request.get_host()
        full_url = f"{protocol}://{host}"

        # Process icon
        iconlink = None
        try:
            iconfile = cd.get('iconfile') or cd.get('iconbase64')
            if iconfile:
                iconlink = save_png(iconfile, myuuid, full_url, "icon.png")
        except Exception as e:
            logger.error(f"Icon processing failed: {e}", exc_info=True)

        # Process logo
        logolink = None
        try:
            logofile = cd.get('logofile') or cd.get('logobase64')
            if logofile:
                logolink = save_png(logofile, myuuid, full_url, "logo.png")
        except Exception as e:
            logger.error(f"Logo processing failed: {e}", exc_info=True)

        # Build custom config
        decodedCustom = {}
        decodedCustom['conn-type'] = direction
        if installation == "installationN":
            decodedCustom['disable-installation'] = 'Y'
        if settings_flag == "settingsN":
            decodedCustom['disable-settings'] = 'Y'
        if appname.lower() != "rustdesk":
            decodedCustom['app-name'] = appname

        decodedCustom['override-settings'] = {}
        decodedCustom['default-settings'] = {}

        if permPass:
            decodedCustom['password'] = permPass

        # Theme handling
        if theme != "system":
            target = decodedCustom['default-settings'] if themeDorO == "default" else decodedCustom['override-settings']
            if platform == "windows-x86":
                target['allow-darktheme'] = 'Y' if theme == "dark" else 'N'
            else:
                target['theme'] = theme

        decodedCustom['enable-lan-discovery'] = 'N' if denyLan else 'Y'
        decodedCustom['allow-auto-disconnect'] = 'Y' if autoClose else 'N'

        # Permissions
        target_perm = decodedCustom['default-settings'] if permissionsDorO == "default" else decodedCustom['override-settings']
        target_perm.update({
            'access-mode': permissionsType,
            'verification-method': 'use-permanent-password' if hidecm else 'use-both-passwords',
            'approve-mode': passApproveMode,
            'allow-hide-cm': 'Y' if hidecm else 'N',
            'allow-remove-wallpaper': 'Y' if cd['removeWallpaper'] else 'N',
            'direct-server': 'Y' if enableDirectIP else 'N',
        })
        for key_name, value in bool_flags.items():
            target_perm[key_name] = 'Y' if value else 'N'

        # Manual overrides
        for line in (cd.get('defaultManual') or '').splitlines():
            if '=' in line:
                k, v = line.split('=', 1)
                decodedCustom['default-settings'][k.strip()] = v.strip()
        for line in (cd.get('overrideManual') or '').splitlines():
            if '=' in line:
                k, v = line.split('=', 1)
                decodedCustom['override-settings'][k.strip()] = v.strip()

        # Encode custom config
        custom_json = json.dumps(decodedCustom)
        encodedCustom = base64.b64encode(custom_json.encode("ascii")).decode("ascii")

        # Extras
        extras = {
            'genurl': getattr(settings, 'GENURL', ''),
            'urlLink': urlLink,
            'downloadLink': downloadLink,
            'delayFix': delayFix,
            'version': version,
            'gdpro': "true",
            'cycleMonitor': cycleMonitor,
            'xOffline': xOffline,
            'removeNewVersionNotif': removeNewVersionNotif,
            'hidePassword': hidePassword,
            'hideMenuBar': hideMenuBar,
            'removeTopNotice': removeTopNotice,
            'password_security_length': password_security_length,
            'compname': compname,
            'upload_token': getattr(settings, 'GH_UPLOAD_TOKEN', ''),
        }
        extra_input = json.dumps(extras)

        # Determine workflow URL
        workflow_map = {
            'windows-x86': 'generator-windows-x86.yml',
            'windows': 'generator-windows.yml',
            'linux': 'generator-linux.yml',
            'android': 'generator-android.yml',
            'macos': 'generator-macos.yml',
        }
        workflow_file = workflow_map.get(platform, 'generator-windows.yml')
        url = f"https://api.github.com/repos/{settings.GHUSER}/{settings.REPONAME}/actions/workflows/{workflow_file}/dispatches"

        # Prepare GitHub Action payload
        data = {
            "ref": "master",
            "inputs": {
                "server": server,
                "key": key,
                "apiServer": apiServer,
                "custom": encodedCustom,
                "uuid": myuuid,
                "iconlink": iconlink or "null",
                "logolink": logolink or "null",
                "appname": appname,
                "extras": extra_input,
                "filename": filename,
            }
        }

        headers = {
            'Accept': 'application/vnd.github+json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {settings.GHBEARER}',
            'X-GitHub-Api-Version': '2022-11-28'
        }

        create_github_run(myuuid, filename, direction, platform)
        response = requests.post(url, json=data, headers=headers)
        logger.info(f"GitHub Action trigger: {response.status_code} for {myuuid}")

        if response.status_code == 204:
            return render(request, 'waiting.html', {
                'filename': filename,
                'uuid': myuuid,
                'status': "InProgress",
                'platform': platform
            })
        else:
            logger.error(f"GitHub API error: {response.text}")
            return JsonResponse({"error": "Failed to start build"}, status=500)

    else:
        form = GenerateForm()
    return render(request, 'generator.html', {'form': form})


def check_for_file(request):
    filename = request.GET.get('filename')
    uuid = request.GET.get('uuid')
    platform = request.GET.get('platform')

    if not all([filename, uuid, platform]):
        raise Http404("Missing parameters")

    gh_run = GithubRun.objects.filter(uuid=uuid).first()
    if not gh_run:
        raise Http404("Build not found")

    if gh_run.status == "Success":
        short_uuid = gh_run.uuid.replace('-', '')[:4]
        return render(request, 'generated.html', {
            'filename': filename,
            'uuid': uuid,
            'platform': platform,
            'short_uuid': short_uuid,
            'direction': gh_run.direction.lower(),
        })
    else:
        return render(request, 'waiting.html', {
            'filename': filename,
            'uuid': uuid,
            'status': gh_run.status,
            'platform': platform,
        })


def download(request):
    uuid_str = request.GET.get('uuid')
    full_filename = request.GET.get('filename')

    if not uuid_str or not full_filename:
        return HttpResponse("Missing UUID or filename", status=400)
    if not re.fullmatch(r'^[a-zA-Z0-9._\-]+$', full_filename):
        return HttpResponse("Invalid filename format", status=400)
    if not any(full_filename.lower().endswith(ext) for ext in ['.exe', '.msi', '.dmg', '.deb', '.apk', '.zip']):
        return HttpResponse("File type not allowed", status=400)

    try:
        UUID(uuid_str)
    except ValueError:
        return HttpResponse("Invalid UUID", status=400)

    gh_run = GithubRun.objects.filter(uuid=uuid_str).first()
    if not gh_run or gh_run.status != "Success":
        return HttpResponse("Build not ready or not found", status=404)

    build_dir = Path(settings.BASE_DIR) / 'exe' / uuid_str
    target_file = build_dir / full_filename

    try:
        target_file = target_file.resolve(strict=False)
        build_dir_resolved = build_dir.resolve()
        target_file.relative_to(build_dir_resolved)
    except (OSError, ValueError):
        return HttpResponse("Access denied", status=403)

    if not target_file.is_file():
        return HttpResponse("File not found", status=404)

    try:
        return FileResponse(open(target_file, 'rb'), as_attachment=True, filename=full_filename)
    except (IOError, OSError):
        return HttpResponse("Failed to read file", status=500)


def get_png(request):
    filename = request.GET.get('filename')
    uuid_str = request.GET.get('uuid')

    if not filename or not uuid_str:
        return HttpResponse("Missing filename or UUID", status=400)
    if not filename.lower().endswith('.png'):
        return HttpResponse("Only PNG files allowed", status=400)
    if not re.fullmatch(r'^[a-zA-Z0-9._\-]+$', filename):
        return HttpResponse("Invalid filename", status=400)

    try:
        UUID(uuid_str)
    except ValueError:
        return HttpResponse("Invalid UUID", status=400)

    png_dir = Path(settings.BASE_DIR) / 'png' / uuid_str
    target_file = png_dir / filename

    try:
        target_file = target_file.resolve(strict=False)
        png_dir_resolved = png_dir.resolve()
        target_file.relative_to(png_dir_resolved)
    except (OSError, ValueError):
        return HttpResponse("Access denied", status=403)

    if not target_file.is_file():
        raise Http404("File not found")

    try:
        with open(target_file, 'rb') as f:
            response = HttpResponse(f.read(), content_type='image/png')
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            return response
    except (IOError, OSError):
        return HttpResponse("Failed to read file", status=500)


@csrf_exempt
@require_http_methods(["POST"])
def update_github_run(request):
    try:
        data = json.loads(request.body)
        myuuid = data.get('uuid')
        mystatus = data.get('status')
        if myuuid and mystatus:
            GithubRun.objects.filter(uuid=myuuid).update(status=mystatus)
        return HttpResponse('')
    except Exception as e:
        logger.error(f"Update run error: {e}")
        return HttpResponse("Bad Request", status=400)


@csrf_exempt
def save_custom_client(request):
    if request.method != 'POST':
        return HttpResponse("Method not allowed", status=405)
    client_token = request.POST.get('token')
    expected_token = getattr(settings, 'GH_UPLOAD_TOKEN', None)

    if not expected_token:
        logger.error("GH_UPLOAD_TOKEN not set in settings!")
        return HttpResponse("Server misconfigured", status=500)

    if client_token != expected_token:
        logger.warning(f"Invalid token: {client_token}")
        return HttpResponse("Forbidden", status=403)
    file = request.FILES.get('file')
    myuuid = request.POST.get('uuid')
    if not file or not myuuid:
        return HttpResponse("Missing file or uuid", status=400)
    exe_dir = Path(settings.BASE_DIR) / "exe" / myuuid
    exe_dir.mkdir(parents=True, exist_ok=True)
    file_path = exe_dir / file.name

    with open(file_path, "wb+") as f:
        for chunk in file.chunks():
            f.write(chunk)
    return HttpResponse("OK", status=200)

@csrf_exempt
@require_http_methods(["POST"])
def startgh(request):

    auth_header = request.META.get('HTTP_AUTHORIZATION')
    expected = f"Bearer {getattr(settings, 'EXTERNAL_API_TOKEN', 'your-secret-token')}"
    if auth_header != expected:
        return HttpResponse("Unauthorized", status=401)

    try:
        data_ = json.loads(request.body)
        platform = data_.get('platform', 'windows')
        workflow_file = {
            'windows-x86': 'generator-windows-x86.yml',
            'windows': 'generator-windows.yml',
            'linux': 'generator-linux.yml',
            'android': 'generator-android.yml',
            'macos': 'generator-macos.yml',
        }.get(platform, 'generator-windows.yml')

        url = f"https://api.github.com/repos/{settings.GHUSER}/{settings.REPONAME}/actions/workflows/{workflow_file}/dispatches"
        headers = {
            'Accept': 'application/vnd.github+json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {settings.GHBEARER}',
            'X-GitHub-Api-Version': '2022-11-28'
        }
        response = requests.post(url, json=data_, headers=headers)
        logger.info(f"External trigger: {response.status_code}")
        return HttpResponse(status=204)
    except Exception as e:
        logger.error(f"startgh error: {e}")
        return HttpResponse("Bad Request", status=400)
