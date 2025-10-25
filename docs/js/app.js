import Templates from './templates.js';

// 配置管理器
const ConfigManager = {
    // 从CSS变量读取数值，如果读取失败则使用默认值
    getCSSValue(propertyName, defaultValue = null) {
        const value = getComputedStyle(document.documentElement)
            .getPropertyValue(propertyName)
            .trim();
        
        if (!value && defaultValue !== null) {
            return defaultValue;
        }
        
        // 处理带单位的值
        if (value.endsWith('px') || value.endsWith('ms') || value.endsWith('s')) {
            return parseFloat(value);
        }
        // 处理小数值
        if (value.includes('.')) {
            return parseFloat(value);
        }
        // 处理整数值
        if (!isNaN(value)) {
            return parseInt(value, 10);
        }
        return value || defaultValue;
    },

    // 获取所有配置
    getConfig() {
        return {
            layout: {
                contentPadding: this.getCSSValue('--content-padding', 12)
            },
            grid: {
                minCardWidth: this.getCSSValue('--grid-min-card-width', 180),
                cardHeight: this.getCSSValue('--grid-card-height', 250),
                gap: this.getCSSValue('--grid-gap', 16),
                columns: this.getCSSValue('--grid-columns', 4),
                bufferRows: this.getCSSValue('--grid-buffer-rows', 2),
                padding: this.getCSSValue('--grid-padding', 12)
            },
            selection: {
                itemHeight: this.getCSSValue('--selection-item-height', 45),
                padding: this.getCSSValue('--selection-item-padding', 16),
                bufferItems: this.getCSSValue('--selection-buffer-items', 20)
            },
            observer: {
                margin: this.getCSSValue('--video-observer-margin', 200),
                threshold: this.getCSSValue('--video-observer-threshold', 0.1)
            },
            badge: {
                size: this.getCSSValue('--badge-size', 24),
                margin: this.getCSSValue('--badge-margin', 8)
            },
            timing: {
                hoverDelay: this.getCSSValue('--hover-delay', 500),
                resizeDebounce: this.getCSSValue('--resize-debounce', 200),
                scrollThrottle: this.getCSSValue('--scroll-throttle', 16),
                transitionDuration: this.getCSSValue('--transition-duration', 200),
                fadeDuration: this.getCSSValue('--fade-duration', 300)
            },
            preview: {
                maxWidth: this.getCSSValue('--preview-card-max-width', 320),
                minWidth: this.getCSSValue('--preview-card-min-width', 240),
                padding: this.getCSSValue('--preview-card-padding', 16),
                offset: this.getCSSValue('--preview-card-offset', 8)
            },
            ui: {
                buttonSize: this.getCSSValue('--button-size', 32),
                iconSize: this.getCSSValue('--icon-size', 16),
                borderRadius: this.getCSSValue('--border-radius', 4)
            },
            loading: {
                batchSize: this.getCSSValue('--loading-batch-size', 150)
            },
            paths: {
                assetsRoot: './assets',
                get datasetInfo() {
                    return `${this.assetsRoot}/dataset_info`;
                },
                get videos() {
                    return `${this.assetsRoot}/videos`;
                }
            }
        };
        
        return config;
    }
};

// 先声明一个变量
let GRID_CONFIG = null;

const APP = {
    // 初始化网格布局的CSS变量
    // 更新动态CSS变量
    updateDynamicGridVariables(cardWidth, columns) {
        document.documentElement.style.setProperty('--grid-card-width', `${cardWidth}px`);
        document.documentElement.style.setProperty('--grid-columns', columns);
        // 确保grid使用与内容相同的内边距
        document.documentElement.style.setProperty('--grid-padding', getComputedStyle(document.documentElement).getPropertyValue('--content-padding'));
    },
    
    datasets: [],
    filteredDatasets: [],
    selectedDatasets: new Set(),
    currentFormat: 'python',
    currentHub: 'modelscope',
    listDatasets: new Set(), 
    filters: {},
    
    // Filter Finder状态
    filterFinderMatches: [],
    filterFinderCurrentIndex: -1,
    
    async init() {
        // 确保加载动画可见
        const loadingOverlay = document.getElementById('loadingOverlay');
        loadingOverlay.classList.remove('hidden');
        
        // 初始化配置
        GRID_CONFIG = ConfigManager.getConfig();
        
        try {
            await this.loadDatasets();

            this.buildDatasetIndex();
            this.buildFilterGroups();
            this.bindEvents();
            this.applyFilters();
        } catch (err) {
            console.error('Initialization failed:', err);
            alert('Failed to initialize application: ' + err.message);
        } finally {
            // 隐藏加载动画
            setTimeout(() => {
                loadingOverlay.classList.add('hidden');
            }, 300); // 延迟300ms让用户看到"完成"状态
        }
    },
    
    async loadDatasets() {
        try {
            const config = ConfigManager.getConfig();
            const indexRes = await fetch(`${config.paths.datasetInfo}/data_index.json`);
            const fileList = await indexRes.json();
            
            const loadingProgress = document.getElementById('loadingProgress');
            const loadingBar = document.getElementById('loadingBar');
            
            console.log(` Starting to load ${fileList.length} datasets...`);
            const startTime = performance.now();
            
            // 更新初始进度
            loadingProgress.textContent = `0 / ${fileList.length}`;
            loadingBar.style.width = '0%';
            
            // 分批加载配置
            const BATCH_SIZE = GRID_CONFIG.loading.batchSize;
            const batches = [];
            
            for (let i = 0; i < fileList.length; i += BATCH_SIZE) {
                batches.push(fileList.slice(i, i + BATCH_SIZE));
            }
            
            console.log(` Split into ${batches.length} batches`);
            
            this.datasets = [];
            let loadedCount = 0;
            
            // 逐批加载
            for (let batchIndex = 0; batchIndex < batches.length; batchIndex++) {
                const batch = batches[batchIndex];
                
                const loadPromises = batch.map(async (fileName) => {
                    try {
                        const res = await fetch(`${config.paths.datasetInfo}/${fileName}`);
                        const yamlText = await res.text();
                        const raw = jsyaml.load(yamlText);
                        
                        return {
                            path: fileName.replace(/\.yml$/i, ''),
                            name: raw.dataset_name || fileName,
                            video_url: `${config.paths.videos}/${fileName.replace(/\.yml$/i, '')}.mp4`,
                            description: raw.task_descriptions || '',
                            scenes: raw.scene_type || [],
                            actions: raw.atomic_actions || [],
                            objects: (raw.objects || []).map(obj => ({
                                name: obj.object_name,
                                hierarchy: [
                                    obj.level1, 
                                    obj.level2, 
                                    obj.level3, 
                                    obj.level4, 
                                    obj.level5
                                ].filter(level => level !== null && level !== undefined),
                                raw: obj
                            })),
                            robot: raw.device_model,
                            endEffector: raw.end_effector_type,
                            platformHeight: raw.operation_platform_height,
                            raw: raw,
                            getAllScenes: function() { return this.scenes; },
                            hasScene: function(sceneType) { return this.scenes.includes(sceneType); },
                            getObjectsByLevel: function(level, value) {
                                return this.objects.filter(obj => obj.hierarchy[level - 1] === value);
                            },
                            getTopLevelCategories: function() {
                                return [...new Set(this.objects.map(obj => obj.hierarchy[0]))];
                            }
                        };
                    } catch (err) {
                        console.error(` Failed to load ${fileName}:`, err);
                        return null;
                    }
                });
                
                const results = await Promise.all(loadPromises);
                const validResults = results.filter(ds => ds !== null);
                this.datasets.push(...validResults);
                
                // 更新进度
                loadedCount += batch.length;
                const progress = Math.floor((loadedCount / fileList.length) * 100);
                loadingProgress.textContent = `${loadedCount} / ${fileList.length}`;
                loadingBar.style.width = `${progress}%`;
                
                console.log(` Batch ${batchIndex + 1}/${batches.length}: Loaded ${validResults.length}/${batch.length} datasets (Total: ${this.datasets.length})`);
            }
            
            // 确保进度条显示100%
            loadingProgress.textContent = `${fileList.length} / ${fileList.length}`;
            loadingBar.style.width = '100%';
            
            const endTime = performance.now();
            const loadTime = (endTime - startTime).toFixed(2);
            
            console.log(` Loaded ${this.datasets.length} datasets in ${loadTime}ms`);
            console.log(` Average: ${(loadTime / this.datasets.length).toFixed(2)}ms per dataset`);
            
        } catch (err) {
            console.error(' Failed to load datasets:', err);
            throw err; // 抛出错误让init函数处理
        }
    },

    debounce(func, wait) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    },
    
    buildFilterGroups() {
        const groups = {
            'scene': { 
                title: 'scene', 
                values: new Set(),
                type: 'flat' // 扁平化多值
            },
            'robot': { 
                title: 'robot', 
                values: new Set(),
                type: 'flat'
            },
            'end': { 
                title: 'end effector', 
                values: new Set(),
                type: 'flat'
            },
            'action': {
                title: 'action',
                values: new Set(),
                type: 'flat'
            },
            'object': {
                title: 'operation object',
                values: new Map(), // 使用 Map 存储层级关系
                type: 'hierarchical' // 层级化
            }
        };
        
        // 收集所有过滤器选项
        this.datasets.forEach(ds => {
            // 扁平化多值字段
            if (ds.scenes) {
                ds.scenes.forEach(scene => groups.scene.values.add(scene));
            }
            if (ds.robot) {
                // robot 可能是数组或单值
                const robots = Array.isArray(ds.robot) ? ds.robot : [ds.robot];
                robots.forEach(r => groups.robot.values.add(r));
            }
            if (ds.endEffector) {
                groups.end.values.add(ds.endEffector);
            }
            if (ds.actions) {
                ds.actions.forEach(action => groups.action.values.add(action));
            }
            
            // 层级化对象字段
            if (ds.objects) {
                ds.objects.forEach(obj => {
                    this.addToHierarchy(groups.object.values, obj.hierarchy);
                });
            }
        });
        
        // 渲染 UI
        const container = document.getElementById('filterGroups');
        container.innerHTML = '';
        
        for (const [key, group] of Object.entries(groups)) {
            const div = document.createElement('div');
            div.className = 'filter-group';
            
            if (group.type === 'flat') {
                div.innerHTML = this.buildFlatFilterGroup(key, group);
            } else if (group.type === 'hierarchical') {
                div.innerHTML = this.buildHierarchicalFilterGroup(key, group);
            }
            
            container.appendChild(div);
            
            // 获取标题元素和标题复选框
            const titleElement = div.querySelector('.filter-group-title');
            const titleLeft = div.querySelector('.filter-group-title-left');
            const titleCheckbox = div.querySelector('.filter-group-title-checkbox input');
            const filterOptions = div.querySelector('.filter-options');
            
            // 点击标题左侧部分进行折叠/展开
            titleLeft.addEventListener('click', () => {
                div.classList.toggle('collapsed');
            });
            
            // 阻止点击复选框区域时触发折叠
            const checkboxArea = div.querySelector('.filter-group-title-checkbox');
            checkboxArea.addEventListener('click', (e) => {
                e.stopPropagation();
            });
            
            // 大类复选框悬停效果
            checkboxArea.addEventListener('mouseenter', () => {
                titleElement.classList.add('highlight-title');
            });
            
            checkboxArea.addEventListener('mouseleave', () => {
                titleElement.classList.remove('highlight-title');
            });
            
            // 大类复选框的change事件
            titleCheckbox.addEventListener('change', (e) => {
                const allCheckboxes = filterOptions.querySelectorAll('input[type="checkbox"]');
                
                if (e.target.checked) {
                    // 选中大类复选框时，取消所有子选项
                    allCheckboxes.forEach(cb => {
                        cb.checked = false;
                    });
                } else {
                    // 取消大类复选框时，不做任何操作（保持当前状态）
                }
                
                this.applyFilters();
            });
            
            // 为扁平化filter添加悬停高亮效果
            if (group.type === 'flat') {
                const checkboxAreas = div.querySelectorAll('.filter-option-checkbox');
                checkboxAreas.forEach(checkboxArea => {
                    checkboxArea.addEventListener('mouseenter', (e) => {
                        const filterOption = checkboxArea.closest('.filter-option');
                        if (filterOption) {
                            filterOption.classList.add('highlight-label');
                        }
                    });
                    
                    checkboxArea.addEventListener('mouseleave', (e) => {
                        const filterOption = checkboxArea.closest('.filter-option');
                        if (filterOption) {
                            filterOption.classList.remove('highlight-label');
                        }
                    });
                    
                    // 子选项复选框change事件：选中任何子选项时取消大类复选框
                    const checkbox = checkboxArea.querySelector('input[type="checkbox"]');
                    checkbox.addEventListener('change', (e) => {
                        if (e.target.checked) {
                            titleCheckbox.checked = false;
                        } else {
                            // 如果所有子选项都未选中，自动勾选大类复选框
                            const checkedCount = filterOptions.querySelectorAll('input[type="checkbox"]:checked').length;
                            if (checkedCount === 0) {
                                titleCheckbox.checked = true;
                            }
                        }
                        this.applyFilters();
                    });
                });
            }
            
            // 添加层级选择交互
            if (group.type === 'hierarchical') {
                this.attachHierarchyListeners(div, titleCheckbox);
            }
        }
    },

    // 辅助函数：将对象层级添加到 Map 中
    addToHierarchy(hierarchyMap, levels) {
        if (!levels || levels.length === 0) return;
        
        let current = hierarchyMap;
        levels.forEach((level, idx) => {
            if (!current.has(level)) {
                current.set(level, {
                    children: new Map(),
                    isLeaf: idx === levels.length - 1
                });
            }
            current = current.get(level).children;
        });
    },

    // 构建扁平化过滤器组 HTML
    buildFlatFilterGroup(key, group) {
        // 使用与层级化过滤器相同的缩进参数
        const baseIndent = ConfigManager.getCSSValue('--hierarchy-indent', 4);
        return Templates.buildFlatFilterGroup(key, group, baseIndent);
    },

    // 构建层级化过滤器组 HTML
    buildHierarchicalFilterGroup(key, group) {
        const buildHierarchyHTML = (map, level = 1, parentPath = '') => {
            let html = '';
            const sortedEntries = Array.from(map.entries()).sort((a, b) => a[0].localeCompare(b[0]));
            const baseIndent = ConfigManager.getCSSValue('--hierarchy-indent', 4);
            
            sortedEntries.forEach(([value, node]) => {
                const fullPath = parentPath ? `${parentPath}>${value}` : value;
                const hasChildren = node.children.size > 0;
                const childrenHTML = hasChildren ? buildHierarchyHTML(node.children, level + 1, fullPath) : '';
                
                html += Templates.buildHierarchyOption(key, value, fullPath, hasChildren, level, baseIndent, childrenHTML);
            });
            
            return html;
        };
        
        return Templates.buildHierarchicalFilterGroup(key, group, buildHierarchyHTML);
    },

    // 添加层级展开/折叠交互
    attachHierarchyListeners(div, titleCheckbox) {
        // 1. 处理层级名称点击展开/折叠
        const nameOnlyElements = div.querySelectorAll('.hierarchy-name-only');
        nameOnlyElements.forEach(nameElement => {
            nameElement.addEventListener('click', (e) => {
                if (e.target.closest('.filter-option-checkbox')) {
                    return;
                }
                
                const wrapper = nameElement.closest('.filter-option-wrapper');
                const children = wrapper.querySelector('.filter-children');
                const toggle = nameElement.querySelector('.hierarchy-toggle');
                
                if (children) {
                    children.classList.toggle('collapsed');
                    toggle.textContent = children.classList.contains('collapsed') ? '▶' : '▼';
                }
            });
        });
        
        // 2. 添加悬停高亮效果
        const allCheckboxAreas = div.querySelectorAll('.filter-option-checkbox');
        allCheckboxAreas.forEach(checkboxArea => {
            checkboxArea.addEventListener('mouseenter', (e) => {
                const filterOption = checkboxArea.closest('.filter-option');
                if (filterOption) {
                    filterOption.classList.add('highlight-label');
                }
            });
            
            checkboxArea.addEventListener('mouseleave', (e) => {
                const filterOption = checkboxArea.closest('.filter-option');
                if (filterOption) {
                    filterOption.classList.remove('highlight-label');
                }
            });
        });
        
        // 3. 处理复选框逻辑
        const filterGroup = div.querySelector('.filter-options');
        const filterType = div.closest('.filter-group').querySelector('input[data-filter]')?.dataset.filter;
        
        const checkboxes = div.querySelectorAll('.filter-options input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const value = e.target.value;
                
                // 任何子选项被选中时，取消大类复选框
                if (e.target.checked) {
                    if (titleCheckbox) {
                        titleCheckbox.checked = false;
                    }
                }
                
                // 如果点击的是子目录All选项
                if (value.endsWith(':ALL')) {
                    if (e.target.checked) {
                        // 选中该子目录下所有叶子节点
                        const wrapper = e.target.closest('.filter-option-wrapper');
                        const childrenDiv = wrapper.querySelector('.filter-children');
                        if (childrenDiv) {
                            const leafCheckboxes = childrenDiv.querySelectorAll('input[type="checkbox"]:not([value$=":ALL"])');
                            leafCheckboxes.forEach(leaf => {
                                leaf.checked = true;
                            });
                        }
                    } else {
                        // 取消子目录All时，取消该子目录下所有叶子节点
                        const wrapper = e.target.closest('.filter-option-wrapper');
                        const childrenDiv = wrapper.querySelector('.filter-children');
                        if (childrenDiv) {
                            const leafCheckboxes = childrenDiv.querySelectorAll('input[type="checkbox"]:not([value$=":ALL"])');
                            leafCheckboxes.forEach(leaf => {
                                leaf.checked = false;
                            });
                        }
                        
                        // 如果所有子选项都未选中，自动勾选大类复选框
                        const checkedCount = filterGroup.querySelectorAll('input[type="checkbox"]:checked').length;
                        if (checkedCount === 0 && titleCheckbox) {
                            titleCheckbox.checked = true;
                        }
                    }
                }
                // 如果点击的是叶子节点
                else {
                    if (e.target.checked) {
                        // 检查同级所有叶子节点是否都选中，如果是则自动勾选父级All
                        const parentWrapper = e.target.closest('.filter-children')?.closest('.filter-option-wrapper');
                        if (parentWrapper) {
                            const parentChildrenDiv = parentWrapper.querySelector('.filter-children');
                            const allLeafs = parentChildrenDiv.querySelectorAll('input[type="checkbox"]:not([value$=":ALL"])');
                            const checkedLeafs = Array.from(allLeafs).filter(cb => cb.checked);
                            
                            if (allLeafs.length === checkedLeafs.length && allLeafs.length > 0) {
                                const parentAll = parentWrapper.querySelector('input[value$=":ALL"]');
                                if (parentAll) {
                                    parentAll.checked = true;
                                }
                            }
                        }
                    } else {
                        // 取消叶子节点时，自动取消父级All
                        const parentWrapper = e.target.closest('.filter-children')?.closest('.filter-option-wrapper');
                        if (parentWrapper) {
                            const parentAll = parentWrapper.querySelector('input[value$=":ALL"]');
                            if (parentAll) {
                                parentAll.checked = false;
                            }
                        }
                        
                        // 如果所有子选项都未选中，自动勾选大类复选框
                        const checkedCount = filterGroup.querySelectorAll('input[type="checkbox"]:checked').length;
                        if (checkedCount === 0 && titleCheckbox) {
                            titleCheckbox.checked = true;
                        }
                    }
                }
                
                // 触发过滤更新
                this.applyFilters();
            });
        });
    },

    // Filter Finder - 筛选项搜索功能
    bindFilterFinderEvents() {
        const input = document.getElementById('filterFinderInput');
        const prevBtn = document.getElementById('filterFinderPrev');
        const nextBtn = document.getElementById('filterFinderNext');
        const clearBtn = document.getElementById('filterFinderClear');
        
        if (!input || !prevBtn || !nextBtn || !clearBtn) return;
        
        // 输入搜索关键词
        input.addEventListener('input', () => {
            this.searchFilterOptions(input.value.trim());
        });
        
        // 上一个匹配
        prevBtn.addEventListener('click', () => {
            this.navigateFilterMatch('prev');
        });
        
        // 下一个匹配
        nextBtn.addEventListener('click', () => {
            this.navigateFilterMatch('next');
        });
        
        // 清空搜索
        clearBtn.addEventListener('click', () => {
            input.value = '';
            this.clearFilterSearch();
        });
        
        // 支持Enter键导航
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                if (e.shiftKey) {
                    this.navigateFilterMatch('prev');
                } else {
                    this.navigateFilterMatch('next');
                }
            } else if (e.key === 'Escape') {
                input.value = '';
                this.clearFilterSearch();
            }
        });
    },
    
    searchFilterOptions(query) {
        // 清除之前的高亮
        this.clearFilterSearch();
        
        if (!query) {
            this.updateFilterFinderUI();
            return;
        }
        
        const filterContent = document.getElementById('filterGroups');
        if (!filterContent) return;
        
        // 查找所有filter-option
        const allOptions = filterContent.querySelectorAll('.filter-option');
        this.filterFinderMatches = [];
        
        allOptions.forEach(option => {
            // 获取选项的文本内容
            const labelElement = option.querySelector('.filter-option-label, .hierarchy-label');
            if (!labelElement) return;
            
            const text = labelElement.textContent.trim();
            
            // 检查是否匹配（不区分大小写）
            if (text.toLowerCase().includes(query.toLowerCase())) {
                option.classList.add('highlight-match');
                this.filterFinderMatches.push({
                    element: option,
                    text: text,
                    wrapper: option.closest('.filter-option-wrapper')
                });
            }
        });
        
        // 如果有匹配，导航到第一个
        if (this.filterFinderMatches.length > 0) {
            this.filterFinderCurrentIndex = 0;
            this.highlightCurrentMatch();
        }
        
        this.updateFilterFinderUI();
    },
    
    navigateFilterMatch(direction) {
        if (this.filterFinderMatches.length === 0) return;
        
        // 移除当前高亮
        if (this.filterFinderCurrentIndex >= 0 && this.filterFinderCurrentIndex < this.filterFinderMatches.length) {
            this.filterFinderMatches[this.filterFinderCurrentIndex].element.classList.remove('current-match');
        }
        
        // 计算新索引
        if (direction === 'next') {
            this.filterFinderCurrentIndex = (this.filterFinderCurrentIndex + 1) % this.filterFinderMatches.length;
        } else {
            this.filterFinderCurrentIndex = (this.filterFinderCurrentIndex - 1 + this.filterFinderMatches.length) % this.filterFinderMatches.length;
        }
        
        this.highlightCurrentMatch();
        this.updateFilterFinderUI();
    },
    
    highlightCurrentMatch() {
        if (this.filterFinderCurrentIndex < 0 || this.filterFinderCurrentIndex >= this.filterFinderMatches.length) {
            return;
        }
        
        const match = this.filterFinderMatches[this.filterFinderCurrentIndex];
        const option = match.element;
        const wrapper = match.wrapper;
        
        // 添加当前匹配高亮
        option.classList.add('current-match');
        
        // 展开所有父级的折叠项
        let parent = option.closest('.filter-children');
        while (parent) {
            if (parent.classList.contains('collapsed')) {
                parent.classList.remove('collapsed');
                
                // 更新三角图标
                const parentWrapper = parent.closest('.filter-option-wrapper');
                if (parentWrapper) {
                    const toggle = parentWrapper.querySelector('.hierarchy-toggle');
                    if (toggle) {
                        toggle.textContent = '▼';
                    }
                }
            }
            parent = parent.parentElement?.closest('.filter-children');
        }
        
        // 展开所在的filter-group
        const filterGroup = option.closest('.filter-group');
        if (filterGroup && filterGroup.classList.contains('collapsed')) {
            filterGroup.classList.remove('collapsed');
        }
        
        // 滚动到可见位置
        const filterContent = document.getElementById('filterGroups');
        if (filterContent && option) {
            const optionRect = option.getBoundingClientRect();
            const contentRect = filterContent.getBoundingClientRect();
            
            // 如果元素不在可见区域内，滚动到它
            if (optionRect.top < contentRect.top || optionRect.bottom > contentRect.bottom) {
                option.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    },
    
    clearFilterSearch() {
        // 移除所有高亮
        document.querySelectorAll('.filter-option.highlight-match').forEach(el => {
            el.classList.remove('highlight-match', 'current-match');
        });
        
        this.filterFinderMatches = [];
        this.filterFinderCurrentIndex = -1;
        this.updateFilterFinderUI();
    },
    
    updateFilterFinderUI() {
        const countElement = document.getElementById('filterFinderCount');
        const prevBtn = document.getElementById('filterFinderPrev');
        const nextBtn = document.getElementById('filterFinderNext');
        
        if (!countElement || !prevBtn || !nextBtn) return;
        
        const total = this.filterFinderMatches.length;
        const current = total > 0 ? this.filterFinderCurrentIndex + 1 : 0;
        
        countElement.textContent = `${current}/${total}`;
        
        // 禁用/启用导航按钮
        const hasMatches = total > 0;
        prevBtn.disabled = !hasMatches;
        nextBtn.disabled = !hasMatches;
    },
    
    // 使用事件委托处理video-grid的所有交互（避免内存泄漏）
    bindVideoGridEvents() {
        const grid = document.getElementById('videoGrid');
        if (!grid) return;
        
        // 事件委托：点击video-card
        grid.addEventListener('click', (e) => {
            // 防止点击视频时触发
            if (e.target.tagName === 'VIDEO') return;
            
            const card = e.target.closest('.video-card');
            if (!card) return;
            
            const path = card.dataset.path;
            if (!path) return;
            
            this.toggleSelection(path);
            this.updateCardStyles();
            this.updateSelectionPanel();
        });
        
        // 事件委托：视频加载错误
        grid.addEventListener('error', (e) => {
            if (e.target.tagName === 'VIDEO') {
                const card = e.target.closest('.video-card');
                if (card) {
                    const errorDiv = card.querySelector('.video-error');
                    if (errorDiv) errorDiv.style.display = 'block';
                }
            }
        }, true); // 使用捕获阶段捕获error事件
    },
    
    // 使用事件委托处理selection-list的所有交互（避免内存泄漏）
    bindSelectionListEvents() {
        const list = document.getElementById('selectionList');
        if (!list) return;
        
        // 悬停定时器（全局共享，避免闭包泄漏）
        let hoverTimer = null;
        let currentHoverPath = null;
        
        // 事件委托：点击事件
        list.addEventListener('click', (e) => {
            const item = e.target.closest('.selection-item');
            if (!item) return;
            
            const path = item.dataset.path;
            if (!path) return;
            
            // 检查是否点击了按钮
            if (e.target.closest('.btn-remove')) {
                e.stopPropagation();
                this.listDatasets.delete(path);
                this._listDatasetsChanged = true;
                this.updateCardStyles();
                this.updateSelectionPanel();
                return;
            }
            
            if (e.target.closest('.btn-detail')) {
                e.stopPropagation();
                this.showDetailModal(path);
                return;
            }
            
            // 点击item本身切换选中状态
            if (this.selectedDatasets.has(path)) {
                this.selectedDatasets.delete(path);
            } else {
                this.selectedDatasets.add(path);
            }
            this.updateCardStyles();
            this.updateSelectionPanel();
        });
        
        // 事件委托：悬停预览
        list.addEventListener('mouseenter', (e) => {
            const item = e.target.closest('.selection-item');
            if (!item) return;
            
            const path = item.dataset.path;
            if (!path) return;
            
            // 如果悬停在按钮上，不显示预览
            if (e.target.closest('.btn-detail, .btn-remove')) {
                return;
            }
            
            // 清除之前的定时器
            if (hoverTimer) {
                clearTimeout(hoverTimer);
            }
            
            currentHoverPath = path;
            
            // 延迟显示预览
            hoverTimer = setTimeout(() => {
                if (currentHoverPath === path) {
                    this.showHoverPreview(path, item);
                }
            }, GRID_CONFIG.timing.hoverDelay);
        }, true); // 使用捕获阶段
        
        list.addEventListener('mouseleave', (e) => {
            const item = e.target.closest('.selection-item');
            if (!item) return;
            
            // 清除定时器
            if (hoverTimer) {
                clearTimeout(hoverTimer);
                hoverTimer = null;
            }
            
            currentHoverPath = null;
            
            // 检查是否移动到预览卡片上
            const relatedTarget = e.relatedTarget;
            const previewCard = document.getElementById('hoverPreviewCard');
            
            if (!previewCard || !previewCard.contains(relatedTarget)) {
                this.hideHoverPreview();
            }
        }, true); // 使用捕获阶段
    },

    bindEvents() {
        document.getElementById('searchBox').addEventListener('input', () => this.applyFilters());
        document.getElementById('resetBtn').addEventListener('click', () => this.resetFilters());
        document.getElementById('selectAllBtn').addEventListener('click', () => this.selectAllFiltered());
        document.getElementById('deselectAllBtn').addEventListener('click', () => this.deselectAllFiltered());
        document.getElementById('importBtn').addEventListener('click', () => this.importSelection());
        document.getElementById('importFile').addEventListener('change', (e) => this.handleImportFile(e));
        document.getElementById('exportBtn').addEventListener('click', () => this.exportSelection());
        document.getElementById('copyCodeBtn').addEventListener('click', () => this.copyCode());
        document.getElementById('addToListBtn').addEventListener('click', () => this.addToList());
        document.getElementById('deleteFromListBtn').addEventListener('click', () => this.deleteFromList());
        document.getElementById('clearListBtn').addEventListener('click', () => this.clearList());
        
        // 使用事件委托处理selection-item的点击和悬停（避免内存泄漏）
        this.bindSelectionListEvents();
        
        // 使用事件委托处理video-grid的点击（避免内存泄漏）
        this.bindVideoGridEvents();
        
        // Filter Finder事件绑定
        this.bindFilterFinderEvents();
        
        document.getElementById('hubSelect').addEventListener('change', (e) => {
            this.currentHub = e.target.value;
            this.updateCodeOutput();
        });
        
        document.querySelectorAll('input[data-filter]').forEach(cb => {
            cb.addEventListener('change', (e) => {
                const filterGroup = e.target.closest('.filter-options');
                const filterType = e.target.dataset.filter;
                
                // 如果点击的是All选项
                if (e.target.value === '__ALL__') {
                    if (e.target.checked) {
                        // 选中All时,取消所有其他选项
                        filterGroup.querySelectorAll(`input[data-filter="${filterType}"]:not([value="__ALL__"])`).forEach(otherCb => {
                            otherCb.checked = false;
                        });
                    }
                } else {
                    // 如果点击的是普通选项
                    if (e.target.checked) {
                        // 选中任何普通选项时,自动取消All
                        const allCheckbox = filterGroup.querySelector(`input[data-filter="${filterType}"][value="__ALL__"]`);
                        if (allCheckbox) {
                            allCheckbox.checked = false;
                        }
                    } else {
                        // 如果取消某个选项后,该组没有任何选项被选中,则自动选中All
                        const checkedCount = filterGroup.querySelectorAll(`input[data-filter="${filterType}"]:not([value="__ALL__"]):checked`).length;
                        if (checkedCount === 0) {
                            const allCheckbox = filterGroup.querySelector(`input[data-filter="${filterType}"][value="__ALL__"]`);
                            if (allCheckbox) {
                                allCheckbox.checked = true;
                            }
                        }
                    }
                }
                
                this.applyFilters();
            });

            // 监听窗口大小变化，重新计算布局
            let resizeTimeout;
            window.addEventListener('resize', () => {
                clearTimeout(resizeTimeout);
                resizeTimeout = setTimeout(() => {
                    this.renderVideoGrid();
                }, 200);  // 防抖：200ms 后重新渲染
            });
            
            // 视频窗格虚拟滚动监听
            const gridContainer = document.querySelector('.video-grid-container');
            let videoSrollTicking = false;
            
            gridContainer.addEventListener('scroll', () => {
                if (!videoSrollTicking) {
                    window.requestAnimationFrame(() => {
                        this.renderVideoGrid();
                        videoSrollTicking = false;
                    });
                    videoSrollTicking = true;
                }
            });

            // 选择列表虚拟滚动监听
            const selectionList = document.getElementById('selectionList');
            let selectionScrollTicking = false;

            selectionList.addEventListener('scroll', () => {
                if (!selectionScrollTicking) {
                    window.requestAnimationFrame(() => {
                        this.updateSelectionPanel();
                        selectionScrollTicking = false;
                    });
                    selectionScrollTicking = true;
                }
            });

        });
        
    },
    
    applyFilters() {
        const query = document.getElementById('searchBox').value.toLowerCase();
        this.filters = {};
        
        // 收集选中的筛选器，但忽略值为__GROUP_ALL__的选项
        document.querySelectorAll('input[data-filter]:checked').forEach(cb => {
            if (cb.value === '__GROUP_ALL__') return; // 跳过大类All选项
            
            const key = cb.dataset.filter;
            if (!this.filters[key]) this.filters[key] = [];
            this.filters[key].push(cb.value);
        });
        
        this.filteredDatasets = this.datasets.filter(ds => {
            if (query && !ds.name.toLowerCase().includes(query)) return false;
            
            for (const [key, values] of Object.entries(this.filters)) {
                let match = false;
                
                if (key === 'scene') {
                    match = ds.scenes && ds.scenes.some(v => values.includes(v));
                } else if (key === 'robot') {
                    const robots = Array.isArray(ds.robot) ? ds.robot : [ds.robot];
                    match = robots.some(r => values.includes(r));
                } else if (key === 'end') {
                    match = values.includes(ds.endEffector);
                } else if (key === 'action') {
                    match = ds.actions && ds.actions.some(a => values.includes(a));
                } else if (key === 'object') {
                    // 检查任何对象的层级路径中是否包含选中的值
                    match = ds.objects && ds.objects.some(obj => 
                        obj.hierarchy.some(h => values.includes(h))
                    );
                }
                
                if (!match) return false;
            }

            return true;
        });
        
        this.updateCounts();
        this.renderVideoGrid();
        this.updateSelectionPanel();
    },

    selectAllFiltered() {
        // 将所有已筛选的数据集添加到选中集合
        this.filteredDatasets.forEach(ds => {
            this.selectedDatasets.add(ds.path);
        });
        
        // 更新UI - 关键是要更新卡片样式
        this.updateCardStyles();
        this.updateSelectionPanel();
    },

    deselectAllFiltered() {
        // 将所有已筛选的数据集从选中集合中移除
        this.filteredDatasets.forEach(ds => {
            this.selectedDatasets.delete(ds.path);
        });
        
        // 更新UI - 关键是要更新卡片样式
        this.updateCardStyles();
        this.updateSelectionPanel();
    },
                
    updateCounts() {
        document.getElementById('filteredCount').textContent = this.filteredDatasets.length;
        
        // 更新筛选器计数
        const counts = {};
        this.filteredDatasets.forEach(ds => {
            // 统计场景
            if (ds.scenes) {
                ds.scenes.forEach(scene => {
                    const countKey = `scene-${scene}`;
                    counts[countKey] = (counts[countKey] || 0) + 1;
                });
            }
            
            // 统计机器人
            if (ds.robot) {
                const robots = Array.isArray(ds.robot) ? ds.robot : [ds.robot];
                robots.forEach(robot => {
                    const countKey = `robot-${robot}`;
                    counts[countKey] = (counts[countKey] || 0) + 1;
                });
            }
            
            // 统计末端执行器
            if (ds.endEffector) {
                const countKey = `end-${ds.endEffector}`;
                counts[countKey] = (counts[countKey] || 0) + 1;
            }
            
            // 统计动作
            if (ds.actions) {
                ds.actions.forEach(action => {
                    const countKey = `action-${action}`;
                    counts[countKey] = (counts[countKey] || 0) + 1;
                });
            }
            
            // 统计对象（包含层级路径）
            if (ds.objects) {
                ds.objects.forEach(obj => {
                    obj.hierarchy.forEach(level => {
                        const fullPath = obj.hierarchy.slice(0, obj.hierarchy.indexOf(level) + 1).join('>');
                        const countKey = `object-${fullPath}`;
                        counts[countKey] = (counts[countKey] || 0) + 1;
                    });
                });
            }
        });
        
        // 为All选项设置计数（等于该筛选器的总数）
        ['scene', 'robot', 'end', 'action', 'object'].forEach(filterType => {
            counts[`${filterType}-__ALL__`] = this.filteredDatasets.length;
        });
        
        document.querySelectorAll('[data-count]').forEach(el => {
            const key = el.dataset.count;
            el.textContent = counts[key] || 0;
        });
    },

    formatMetaTags(ds) {
        const tags = [];
        
        // 场景（只显示第一个）
        if (ds.scenes && ds.scenes.length > 0) {
            const more = ds.scenes.length > 1 ? `+${ds.scenes.length - 1}` : '';
            tags.push(Templates.buildVideoTag(ds.scenes[0], more));
        }
        
        // 机器人型号（只显示第一个）
        if (ds.robot) {
            const robots = Array.isArray(ds.robot) ? ds.robot : [ds.robot];
            const more = robots.length > 1 ? `+${robots.length - 1}` : '';
            tags.push(Templates.buildVideoTag(robots[0], more));
        }
        
        // 末端执行器
        if (ds.endEffector) {
            tags.push(Templates.buildVideoTag(ds.endEffector));
        }
        
        return tags.join('');
    },

    formatHoverOverlay(ds) {
        return Templates.buildHoverOverlay(ds);
    },

    // 格式化tooltip文本
    formatTooltipText(ds) {
        const info = [];
        
        if (ds.scenes && ds.scenes.length > 0) {
            info.push(`场景: ${ds.scenes.join(', ')}`);
        }
        
        if (ds.robot) {
            const robots = Array.isArray(ds.robot) ? ds.robot : [ds.robot];
            info.push(`型号: ${robots.join(', ')}`);
        }
        
        if (ds.endEffector) {
            info.push(`执行器: ${ds.endEffector}`);
        }
        
        if (ds.actions && ds.actions.length > 0) {
            info.push(`动作: ${ds.actions.join(', ')}`);
        }
        
        if (ds.objects && ds.objects.length > 0) {
            const objectChains = ds.objects.map(obj => obj.hierarchy.join('-'));
            info.push(`对象: ${objectChains.join(', ')}`);
        }
        
        return info.join('\n');
    },
    
    renderVideoGrid() {
        const grid = document.getElementById('videoGrid');
        if (!grid) return;
        
        const container = grid.parentElement;
        if (!container) return;
        
        // 计算布局参数
        const gridWidth = grid.clientWidth;
        
        // 使用配置计算布局
        const itemsPerRow = Math.max(1, Math.floor((gridWidth + GRID_CONFIG.grid.gap) / (GRID_CONFIG.grid.minCardWidth + GRID_CONFIG.grid.gap)));
        
        // 计算实际卡片宽度并更新CSS变量
        const cardWidth = Math.floor((gridWidth - GRID_CONFIG.grid.gap * (itemsPerRow - 1)) / itemsPerRow);
        
        // 更新动态CSS变量
        this.updateDynamicGridVariables(cardWidth, itemsPerRow);
        
        // 使用配置中的高度计算总高度
        const itemHeight = GRID_CONFIG.grid.cardHeight + GRID_CONFIG.grid.gap;
        
        // 计算可见范围（增加缓冲区）
        const scrollTop = container.scrollTop;
        const containerHeight = container.clientHeight;
        
        const startRow = Math.max(0, Math.floor(scrollTop / itemHeight) - GRID_CONFIG.grid.bufferRows);
        const endRow = Math.ceil((scrollTop + containerHeight) / itemHeight) + GRID_CONFIG.grid.bufferRows;
        const startIndex = startRow * itemsPerRow;
        const endIndex = Math.min(this.filteredDatasets.length, endRow * itemsPerRow);
        
        // 设置grid总高度（关键！保持滚动条）
        const totalRows = Math.ceil(this.filteredDatasets.length / itemsPerRow);
        grid.style.height = `${totalRows * itemHeight}px`;
        
        // 初始化视频卡片索引缓存
        if (!this._videoCardIndex) {
            this._videoCardIndex = new Map();
        }
        
        // 获取可见数据集
        const visibleDatasets = this.filteredDatasets.slice(startIndex, endIndex);
        const visiblePaths = new Set(visibleDatasets.map(ds => ds.path));
        
        // 移除不可见的卡片
        const existingCards = grid.querySelectorAll('.video-card');
        existingCards.forEach(card => {
            const path = card.dataset.path;
            if (!visiblePaths.has(path)) {
                const video = card.querySelector('video');
                if (video && this.videoObserver) {
                    this.videoObserver.unobserve(video);
                    video.dataset.observed = '';
                }
                card.remove();
                this._videoCardIndex.delete(path);  // 从缓存中移除
            } else {
                this._videoCardIndex.set(path, card);  // 更新缓存
            }
        });
        
        // 添加/更新可见卡片
        const fragment = document.createDocumentFragment();
        visibleDatasets.forEach((ds, i) => {
            const globalIndex = startIndex + i;
            const row = Math.floor(globalIndex / itemsPerRow);
            const col = globalIndex % itemsPerRow;
            
            // 优化：使用缓存查找，避免重复querySelector
            let card = this._videoCardIndex.get(ds.path);
            const isNewCard = !card;
            
            if (isNewCard) {
                card = this.createVideoCard(ds);
            }
            
            // 设置绝对定位和尺寸（关键！）
            card.style.position = 'absolute';
            card.style.left = `${col * (cardWidth + GRID_CONFIG.grid.gap)}px`;
            card.style.top = `${row * itemHeight}px`;
            // 使用CSS变量控制卡片尺寸
            card.style.width = 'var(--grid-card-width)';
            card.style.height = 'var(--grid-card-height)';
            
            // 更新卡片状态
            this.updateCardState(card, ds);
            
            if (isNewCard) {
                // 将新卡片加入缓存
                this._videoCardIndex.set(ds.path, card);
                fragment.appendChild(card);
            }
        });
        
        // 批量添加新卡片
        if (fragment.hasChildNodes()) {
            grid.appendChild(fragment);
        }
        
        // 观察视频元素
        this.observeVideos();
    },

    // 创建单个卡片（避免重复代码）
    createVideoCard(ds) {
        const card = document.createElement('div');
        card.className = 'video-card';
        card.dataset.path = ds.path;
        if (this.selectedDatasets.has(ds.path)) card.classList.add('selected');
        
        card.innerHTML = Templates.buildVideoCard(
            ds, 
            this.formatMetaTags.bind(this), 
            this.formatHoverOverlay.bind(this), 
            this.listDatasets
        );
        
        // 事件监听器已通过事件委托在 bindVideoGridEvents() 中处理
        // 不再为每个card单独添加事件监听器，避免内存泄漏
        
        return card;
    },

    observeVideos() {
    if (!this.videoObserver) {
        const config = ConfigManager.getConfig();
        this.videoObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                const video = entry.target;
                if (entry.isIntersecting) {
                    // 懒加载视频
                    const source = video.querySelector('source');
                    if (source && source.dataset.src) {
                        source.src = source.dataset.src;
                        video.load();
                        video.play().catch(() => {
                            // 自动播放失败是正常的,静默处理
                        });
                        delete source.dataset.src;
                    } else if (video.paused) {
                        // 如果已加载但暂停,尝试播放
                        video.play().catch(() => {});
                    }
                } else {
                    // 离开视口时暂停
                    video.pause();
                }
            });
        }, { 
            rootMargin: `${config.observer.margin}px`, // 提前加载距离
            threshold: config.observer.threshold // 可见比例触发阈值
        });
    }
    
    // 只观察新的video元素
    document.querySelectorAll('.video-thumbnail video').forEach(video => {
        // 避免重复观察
        if (!video.dataset.observed) {
            this.videoObserver.observe(video);
            video.dataset.observed = 'true';
        }
    });
},

    // 只更新卡片状态（不重建DOM）
    updateCardState(card, ds) {
        // 高效更新类名
        const shouldBeSelected = this.selectedDatasets.has(ds.path);
        const isSelected = card.classList.contains('selected');
        
        if (shouldBeSelected !== isSelected) {
            card.classList.toggle('selected', shouldBeSelected);
        }
        
        // 高效更新徽章
        const shouldHaveBadge = this.listDatasets.has(ds.path);
        const badge = card.querySelector('.video-success-badge');
        
        if (shouldHaveBadge && !badge) {
            card.querySelector('.video-thumbnail').insertAdjacentHTML(
                'beforeend', 
                Templates.buildVideoSuccessBadge()
            );
        } else if (!shouldHaveBadge && badge) {
            badge.remove();
        }
    },

    updateCardStyles() {
        // 使用 requestAnimationFrame 批量更新DOM
        if (this.updateStylesScheduled) return;
        
        this.updateStylesScheduled = true;
        requestAnimationFrame(() => {
            const cards = document.querySelectorAll('.video-card');
            
            // 批量读取
            const updates = [];
            cards.forEach(card => {
                const path = card.dataset.path;
                if (!path) return;
                
                const shouldBeSelected = this.selectedDatasets.has(path);
                const shouldHaveBadge = this.listDatasets.has(path);
                
                updates.push({ card, path, shouldBeSelected, shouldHaveBadge });
            });
            
            // 批量写入
            updates.forEach(({ card, path, shouldBeSelected, shouldHaveBadge }) => {
                // 更新选中状态
                card.classList.toggle('selected', shouldBeSelected);
                
                // 更新徽章
                const badge = card.querySelector('.video-success-badge');
                const thumbnail = card.querySelector('.video-thumbnail');
                
                if (shouldHaveBadge && !badge) {
                    thumbnail.insertAdjacentHTML('beforeend', Templates.buildVideoSuccessBadge());
                } else if (!shouldHaveBadge && badge) {
                    badge.remove();
                }
            });
            
            this.updateStylesScheduled = false;
        });
    },
    
    toggleSelection(path) {
        if (this.selectedDatasets.has(path)) {
            this.selectedDatasets.delete(path);
        } else {
            this.selectedDatasets.add(path);
        }
    },
    
    updateSelectionPanel() {
        document.getElementById('selectedCount').textContent = this.selectedDatasets.size;
        document.getElementById('selectionCount').textContent = this.listDatasets.size;
        
        const list = document.getElementById('selectionList');
        if (!list) return;
        
        // **优化: 使用缓存的排序结果**
        if (!this._sortedPathsCache || this._listDatasetsChanged) {
            this._sortedPathsCache = Array.from(this.listDatasets).sort();
            this._listDatasetsChanged = false;
        }
        const sortedPaths = this._sortedPathsCache;
        
        if (sortedPaths.length === 0) {
            list.innerHTML = Templates.buildEmptyCartHint();
            this._virtualContainer = null;  // 清空容器缓存
            this._selectionItemCache = null;  // 清空元素缓存
            this.updateCodeOutput();
            return;
        }
        
        if (!this.datasetMap) {
            this.buildDatasetIndex();
        }
        
        const itemHeight = GRID_CONFIG.selection.itemHeight;
        const scrollTop = list.scrollTop;
        const containerHeight = list.clientHeight;
        const bufferItems = GRID_CONFIG.selection.bufferItems;
        const totalItems = sortedPaths.length;
        const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - bufferItems);
        const visibleCount = Math.ceil(containerHeight / itemHeight);
        const endIndex = Math.min(totalItems, startIndex + visibleCount + bufferItems * 2);
        
        // **优化: 智能缓存容器引用**
        let container = this._virtualContainer;
        
        // 关键修复：检查缓存的容器是否还在DOM中
        if (!container || !document.contains(container)) {
            container = list.querySelector('.selection-virtual-container');
            if (!container) {
                container = document.createElement('div');
                container.className = 'selection-virtual-container';
                // 样式由CSS控制，不需要内联样式
                list.innerHTML = '';
                list.appendChild(container);
            }
            this._virtualContainer = container;  // 更新缓存
        }
        
        const totalHeight = totalItems * itemHeight;
        container.style.height = `${totalHeight}px`;
        
        const visiblePaths = sortedPaths.slice(startIndex, endIndex);
        const visiblePathsSet = new Set(visiblePaths);
        
        // 初始化元素缓存
        if (!this._selectionItemCache) {
            this._selectionItemCache = new Map();
        }
        
        // 移除不可见的元素
        const existingItems = container.querySelectorAll('.selection-item');
        existingItems.forEach(item => {
            const path = item.dataset.path;
            if (!visiblePathsSet.has(path)) {
                item.remove();
                this._selectionItemCache.delete(path);  // 从缓存中移除
            } else {
                this._selectionItemCache.set(path, item);  // 更新缓存
            }
        });
        
        const fragment = document.createDocumentFragment();
        visiblePaths.forEach((path, i) => {
            const globalIndex = startIndex + i;
            const ds = this.datasetMap.get(path);
            if (!ds) return;
            
            // 优化: 使用缓存查找，避免重复querySelector
            let item = this._selectionItemCache.get(path);
            const isNewItem = !item;
            
            if (isNewItem) {
                item = document.createElement('div');
                item.className = 'selection-item';
                item.dataset.path = path;
                
                item.innerHTML = Templates.buildSelectionItem(ds);
                
                // 事件监听器已通过事件委托在 bindSelectionListEvents() 中处理
                // 不再为每个item单独添加事件监听器，避免内存泄漏
                
                // 将新元素加入缓存
                this._selectionItemCache.set(path, item);
            }
            
            // 只设置位置，其他样式通过CSS变量控制
            item.style.top = `${globalIndex * itemHeight}px`;
            
            item.classList.toggle('selected', this.selectedDatasets.has(path));
            
            if (isNewItem) {
                fragment.appendChild(item);
            }
        });
        
        if (fragment.hasChildNodes()) {
            container.appendChild(fragment);
        }
        
        this.updateCodeOutput();
    },
    
    updateCodeOutput() {
        // **优化1: 使用防抖延迟更新，避免频繁操作**
        if (this._codeUpdateTimer) {
            clearTimeout(this._codeUpdateTimer);
        }
        
        this._codeUpdateTimer = setTimeout(() => {
            const output = document.getElementById('codeOutput');
            
            // **优化2: 缓存排序结果，避免重复排序**
            if (!this._sortedPathsCache || this._listDatasetsChanged) {
                this._sortedPathsCache = Array.from(this.listDatasets).sort();
                this._listDatasetsChanged = false;
            }
            
            // **优化3: 使用更高效的字符串拼接**
            const dsListContent = this._sortedPathsCache.join(' \\\n');
            
            // **优化4: 使用 requestAnimationFrame 避免阻塞**
            requestAnimationFrame(() => {
                output.textContent = `python -m robotcoin.datasets.download --hub ${this.currentHub} --ds_lists \\\n${dsListContent}`;
            });
        }, 100); // 100ms防抖
    },
    
    resetFilters() {
        // 清空搜索框
        document.getElementById('searchBox').value = '';
        
        // 首先确保所有大类（组级别）的ALL选项已选中
        const groupAllCheckboxes = document.querySelectorAll('input[data-filter][value="__GROUP_ALL__"]');
        groupAllCheckboxes.forEach(cb => {
            cb.checked = true;
        });
        
        // 取消所有普通筛选选项的选中状态（但保留__GROUP_ALL__）
        document.querySelectorAll('input[data-filter]:not([value="__GROUP_ALL__"])').forEach(cb => {
            cb.checked = false;
        });
        
        // 折叠所有层级选项（如果有展开的）
        document.querySelectorAll('.filter-children').forEach(children => {
            children.classList.add('collapsed');
        });
        document.querySelectorAll('.hierarchy-toggle').forEach(toggle => {
            toggle.textContent = '▶';
        });
        
        // 确保在所有操作完成后，再次强制设置所有大类ALL选项为选中状态
        // 这样可以覆盖任何可能由change事件触发的自动取消选中
        requestAnimationFrame(() => {
            groupAllCheckboxes.forEach(cb => {
                cb.checked = true;
            });
            // 重新应用筛选
            this.applyFilters();
        });
    },
    
    clearSelection() {
        this.selectedDatasets.clear();
        this.renderVideoGrid();
        this.updateSelectionPanel();
    },

    addToList() {
        // 将当前选中的数据集添加到列表
        this.selectedDatasets.forEach(path => {
            this.listDatasets.add(path);
        });
        this._listDatasetsChanged = true; // 标记缓存失效
        this.updateCardStyles();
        this.updateSelectionPanel();
        this._sortedPathsCache = null; // 清理缓存
    },

    deleteFromList() {
        // 从列表中删除当前选中的数据集
        this.selectedDatasets.forEach(path => {
            this.listDatasets.delete(path);
        });
        this._listDatasetsChanged = true; // 标记缓存失效
        this.updateCardStyles();
        this.updateSelectionPanel();
        this._sortedPathsCache = null; // 清理缓存
    },

    clearList() {
        // 清空列表
        this.listDatasets.clear();
        this._listDatasetsChanged = true; // 标记缓存失效
        this.updateCardStyles(); 
        this.updateSelectionPanel();
        this._sortedPathsCache = null; // 清理缓存
    },

    importSelection() {
        document.getElementById('importFile').click();
    },

    handleImportFile(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const imported = JSON.parse(e.target.result);
                
                // 验证导入的数据是否为数组
                if (!Array.isArray(imported)) {
                    alert('Invalid JSON format. Expected an array of dataset IDs.');
                    return;
                }
                
                // 清空当前选择
                this.listDatasets.clear();
                
                // 添加导入的数据集（仅添加存在的数据集）
                let validCount = 0;
                let invalidCount = 0;
                
                imported.forEach(path => {
                    const exists = this.datasets.some(ds => ds.path === path);
                    if (exists) {
                        this.listDatasets.add(path);
                        validCount++;
                    } else {
                        invalidCount++;
                    }
                });
                
                // 更新UI
                this._listDatasetsChanged = true; // 标记缓存失效
                this.renderVideoGrid();
                this.updateSelectionPanel();
                
                // 提示导入结果
                alert(`Import completed!\nValid: ${validCount}\nInvalid/Not found: ${invalidCount}`);
                
            } catch (err) {
                alert('Failed to parse JSON file: ' + err.message);
            }
            
            // 重置文件输入，允许重复导入同一文件
            event.target.value = '';
        };
        
        reader.readAsText(file);
        this._sortedPathsCache = null; // 清理缓存
    },
    
    exportSelection() {
        const blob = new Blob([JSON.stringify(Array.from(this.listDatasets), null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const timestamp = new Date().toISOString().slice(0,10); // 只取日期
        const count = this.listDatasets.size;
        a.download = `robocoin_${count}ds_${timestamp}.json`;
        a.click();
    },
    
    copyCode() {
        const output = document.getElementById('codeOutput');
        const btn = document.getElementById('copyCodeBtn');
        
        // 如果按钮已经是success状态，不执行任何操作
        if (btn.classList.contains('success')) {
            return;
        }
        
        const originalText = btn.textContent;
        
        navigator.clipboard.writeText(output.textContent).then(() => {
            // 修改按钮样式和文字
            btn.classList.add('success');
            btn.textContent = '👍 Copied!';
            
            // 1.5秒后恢复原状
            setTimeout(() => {
                btn.textContent = originalText;
                btn.classList.remove('success');
            }, 1500);
        }).catch(err => {
            alert('复制失败: ' + err.message);
        });
    },

    buildDatasetIndex() {
        // 建立path到dataset的映射
        // 优化右侧selectionPanel查找性能，构建映射map
        this.datasetMap = new Map();
        this.datasets.forEach(ds => {
            this.datasetMap.set(ds.path, ds);
        });
        console.log('✓ 数据集索引已建立:', this.datasetMap.size, '项');
    },

    showDetailModal(datasetPath) {
        const dataset = this.datasetMap.get(datasetPath);
        if (!dataset) return;
        
        // 创建遮罩层
        let overlay = document.getElementById('detailModalOverlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'detailModalOverlay';
            overlay.className = 'detail-modal-overlay';
            document.body.appendChild(overlay);
            
            // 点击遮罩层关闭
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    this.hideDetailModal();
                }
            });
        }
        
        // 创建模态框内容
        overlay.innerHTML = Templates.buildDetailModal(dataset);
        
        // 绑定关闭按钮事件
        overlay.querySelector('.detail-modal-close').addEventListener('click', () => {
            this.hideDetailModal();
        });
        
        // 显示模态框
        requestAnimationFrame(() => {
            overlay.classList.add('visible');
        });
        
        // ESC键关闭
        this._detailModalEscHandler = (e) => {
            if (e.key === 'Escape') {
                this.hideDetailModal();
            }
        };
        document.addEventListener('keydown', this._detailModalEscHandler);
    },

    hideDetailModal() {
        const overlay = document.getElementById('detailModalOverlay');
        if (overlay) {
            overlay.classList.remove('visible');
            setTimeout(() => {
                overlay.remove();
            }, 300);
        }
        
        // 移除ESC键监听
        if (this._detailModalEscHandler) {
            document.removeEventListener('keydown', this._detailModalEscHandler);
            this._detailModalEscHandler = null;
        }
    },

    showHoverPreview(datasetPath, itemElement) {
        const dataset = this.datasetMap.get(datasetPath);
        if (!dataset) return;
        
        // 移除旧的预览卡片
        this.hideHoverPreview();
        
        // 获取item元素的位置信息
        const itemRect = itemElement.getBoundingClientRect();
        
        // 创建预览卡片
        const card = document.createElement('div');
        card.id = 'hoverPreviewCard';
        card.className = 'hover-preview-card';
        
        card.innerHTML = Templates.buildHoverPreview(dataset);
        
        document.body.appendChild(card);
        
        // 卡片尺寸
        const cardWidth = 320;
        const cardHeight = 240;
        
        // 按钮区域宽度（详情按钮 + 删除按钮 + 间距，约60px）
        const buttonAreaWidth = 60;
        
        // 智能定位策略
        let x, y;
        
        // 策略1：优先显示在item左侧（最佳方案，不遮挡任何内容）
        const leftX = itemRect.left - cardWidth - 15;
        
        if (leftX >= 10) {
            // 左侧有足够空间
            x = leftX;
            y = itemRect.top;
        } else {
            // 策略2：左侧空间不足，尝试显示在item内部左侧（但不遮挡按钮）
            const maxSafeX = itemRect.right - buttonAreaWidth - cardWidth - 10;
            
            if (maxSafeX >= itemRect.left + 10) {
                // 可以在item内部左侧安全显示
                x = maxSafeX;
                y = itemRect.top;
            } else {
                // 策略3：水平方向无法安全放置，尝试上方
                x = itemRect.left;
                y = itemRect.top - cardHeight - 10;
                
                // 策略4：上方空间也不足，放置在下方
                if (y < 10) {
                    y = itemRect.bottom + 10;
                }
            }
        }
        
        // 最终边界检查，确保不超出视口
        x = Math.max(10, Math.min(x, window.innerWidth - cardWidth - 10));
        y = Math.max(10, Math.min(y, window.innerHeight - cardHeight - 10));
        
        card.style.left = x + 'px';
        card.style.top = y + 'px';
        
        // 添加鼠标悬停在预览卡片上的事件（保持显示）
        card.addEventListener('mouseenter', () => {
            // 鼠标进入预览卡片，保持显示
        });
        
        card.addEventListener('mouseleave', () => {
            // 鼠标离开预览卡片，隐藏
            this.hideHoverPreview();
        });
        
        // 显示卡片（带动画）
        requestAnimationFrame(() => {
            card.classList.add('visible');
        });
    },

    hideHoverPreview() {
        const card = document.getElementById('hoverPreviewCard');
        if (card) {
            card.remove();
        }
    },

};
export default APP;