"""
小陆 Skill Hub - 技能市场
用户可以安装各种技能扩展小陆的能力
"""
import os
import subprocess
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()


class SkillHub:
    """技能中心 - 管理小陆的技能"""

    # 预设技能列表
    PRESET_SKILLS = {
        'image-analysis': {
            'name': '图片分析',
            'description': '分析图片内容，识别人物、物品、场景',
            'icon': '🖼️',
            'enabled': True,  # 内置功能
        },
        'speech-coach': {
            'name': '嘴替教练',
            'description': '教你怎么说话、人际交往、达成目标',
            'icon': '💬',
            'enabled': True,  # 内置功能
        },
        'ai-tutor': {
            'name': 'AI教练',
            'description': '教你用AI、学习AI、用AI提升效率',
            'icon': '🤖',
            'enabled': True,  # 内置功能
        },
        'weather': {
            'name': '天气查询',
            'description': '查询天气预报，给出出行建议',
            'icon': '🌤️',
            'command': '/skill weather',
            'installed': False,
        },
        'news': {
            'name': '新闻摘要',
            'description': '每日新闻早报，行业动态',
            'icon': '📰',
            'command': '/skill news',
            'installed': False,
        },
        'schedule': {
            'name': '日程管理',
            'description': '管理日程、设置提醒',
            'icon': '📅',
            'command': '/skill schedule',
            'installed': False,
        },
        'translate': {
            'name': '翻译助手',
            'description': '中英互译，文章翻译',
            'icon': '🌐',
            'command': '/translate 你好世界',
            'installed': False,
        },
        'code': {
            'name': '代码助手',
            'description': '写代码、debug、解释代码',
            'icon': '💻',
            'command': '/code def fibonacci',
            'installed': False,
        },
        'writing': {
            'name': '写作助手',
            'description': '写文章、文案、邮件',
            'icon': '✍️',
            'command': '/write 写一封求职邮件',
            'installed': False,
        },
        'health': {
            'name': '健康顾问',
            'description': '饮食建议、运动计划',
            'icon': '🏃',
            'command': '/skill health',
            'installed': False,
        },
    }

    def __init__(self):
        self.skills_dir = os.path.join(os.path.dirname(__file__), 'skills')
        self.installed = self._load_installed()

    def _load_installed(self) -> Dict:
        """加载已安装技能"""
        installed_file = os.path.join(self.skills_dir, 'installed.json')
        if os.path.exists(installed_file):
            import json
            with open(installed_file) as f:
                return json.load(f)
        return {}

    def _save_installed(self):
        """保存已安装技能"""
        installed_file = os.path.join(self.skills_dir, 'installed.json')
        os.makedirs(self.skills_dir, exist_ok=True)
        import json
        with open(installed_file, 'w') as f:
            json.dump(self.installed, f, ensure_ascii=False, indent=2)

    def get_all_skills(self) -> List[Dict]:
        """获取所有技能列表"""
        result = []
        for key, skill in self.PRESET_SKILLS.items():
            is_enabled = skill.get('enabled', False)
            is_installed = key in self.installed or skill.get('installed', False)
            result.append({
                'id': key,
                'name': skill['name'],
                'description': skill['description'],
                'icon': skill['icon'],
                'enabled': is_enabled,
                'installed': is_installed,
            })
        return result

    def get_enabled_skills(self) -> List[str]:
        """获取已启用技能"""
        return [k for k, v in self.PRESET_SKILLS.items() if v.get('enabled')] + list(self.installed.keys())

    def install_skill(self, skill_id: str) -> Dict:
        """安装技能"""
        if skill_id not in self.PRESET_SKILLS:
            return {'success': False, 'message': f'未找到技能: {skill_id}'}

        if skill_id in self.installed:
            return {'success': False, 'message': '该技能已安装'}

        skill = self.PRESET_SKILLS[skill_id]

        # 内置技能直接启用
        if skill.get('enabled'):
            return {'success': True, 'message': f'{skill["name"]} 已启用'}

        # 外部技能通过 skillhub 安装
        try:
            # 这里调用 skillhub_install
            result = subprocess.run(
                ['skillhub', 'install', skill_id],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                self.installed[skill_id] = {
                    'name': skill['name'],
                    'installed_at': str(subprocess.os.times()),
                }
                self._save_installed()
                return {'success': True, 'message': f'{skill["name"]} 安装成功'}
            else:
                return {'success': False, 'message': f'安装失败: {result.stderr}'}
        except FileNotFoundError:
            return {'success': False, 'message': '请先安装 SkillHub CLI'}
        except Exception as e:
            return {'success': False, 'message': f'安装失败: {str(e)}'}

    def uninstall_skill(self, skill_id: str) -> Dict:
        """卸载技能"""
        if skill_id not in self.installed:
            return {'success': False, 'message': '该技能未安装'}

        del self.installed[skill_id]
        self._save_installed()
        return {'success': True, 'message': '技能已卸载'}

    def is_skill_command(self, text: str) -> Optional[str]:
        """检查是否是技能命令"""
        # 内置技能检测
        if '嘴替' in text or '不知道怎么' in text:
            return 'speech-coach'
        if 'AI' in text and ('怎么用' in text or '提升效率' in text or '学习' in text):
            return 'ai-tutor'
        if any(k in text for k in ['人际', '同事', '领导', '社交', '沟通']):
            return 'speech-coach'

        # 技能命令检测
        if text.startswith('/skill '):
            skill_name = text.replace('/skill ', '').strip()
            for sid, skill in self.PRESET_SKILLS.items():
                if skill_name.lower() in skill['name'].lower():
                    return sid

        if text.startswith('/weather'):
            return 'weather'
        if text.startswith('/news'):
            return 'news'
        if text.startswith('/translate'):
            return 'translate'
        if text.startswith('/code'):
            return 'code'
        if text.startswith('/write'):
            return 'writing'

        return None
