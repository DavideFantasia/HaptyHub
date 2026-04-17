package com.example.digitaltwinflowchart // CHANGE THIS IF YOUR PACKAGE IS DIFFERENT!

import android.os.Bundle
import android.speech.tts.TextToSpeech
import android.widget.Button
import android.widget.FrameLayout
import androidx.appcompat.app.AppCompatActivity
import androidx.activity.result.contract.ActivityResultContracts
import org.json.JSONObject
import java.io.InputStream
import java.util.Locale
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min

class MainActivity : AppCompatActivity(), TextToSpeech.OnInitListener {

    private lateinit var tts: TextToSpeech
    private lateinit var canvas: FrameLayout

    // --- ADDED: THE FILE PICKER ---
    // This listens for when the user selects a file from their device storage
    private val pickFileLauncher = registerForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        if (uri != null) {
            try {
                // Open the file the user selected and read it as text
                val inputStream = contentResolver.openInputStream(uri)
                val newJsonString = inputStream?.bufferedReader().use { it?.readText() }

                if (newJsonString != null) {
                    println("Loaded new JSON from user!")
                    drawFlowchart(newJsonString) // Draw the new flowchart!
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        tts = TextToSpeech(this, this)

        window.addFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        hideSystemBars()

        androidx.core.view.WindowCompat.setDecorFitsSystemWindows(window, false)
        val windowInsetsController = androidx.core.view.WindowCompat.getInsetsController(window, window.decorView)
        windowInsetsController.hide(androidx.core.view.WindowInsetsCompat.Type.systemBars())
        windowInsetsController.systemBarsBehavior = androidx.core.view.WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE

        setContentView(R.layout.activity_main)
        canvas = findViewById(R.id.canvas_layout)

        // --- ADDED: THE TRIGGER ---
        // If the user long-presses anywhere on the empty background, open the file picker!
        canvas.setOnLongClickListener {
            tts.speak("Select a file", TextToSpeech.QUEUE_FLUSH, null, "")
            pickFileLauncher.launch("*/*") // Open the file picker for any file type
            true
        }

        // Load the default internal JSON file when the app first opens
        try {
            val inputStream: InputStream = assets.open("output_coordinates.json")
            val defaultJsonString = inputStream.bufferedReader().use { it.readText() }
            drawFlowchart(defaultJsonString)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    // --- ADDED: REUSABLE DRAWING FUNCTION ---
    // All your math is moved here so we can run it multiple times!
    private fun drawFlowchart(jsonString: String) {

        // 1. Wipe the canvas clean of any old buttons!
        canvas.removeAllViews()

        val displayMetrics = resources.displayMetrics
        val xdpi = displayMetrics.xdpi
        val ydpi = displayMetrics.ydpi

        fun mmToPixelsX(mm: Float): Int = ((mm / 25.4f) * xdpi).toInt()
        fun mmToPixelsY(mm: Float): Int = ((mm / 25.4f) * ydpi).toInt()

        val baseWidthMM = 135f
        val baseHeightMM = 217f
        val blockSizeMM = 17f
        val marginXMM = 10f
        val marginYMM = 10f

        val safeMarginX = marginXMM + (blockSizeMM / 2f)
        val safeMarginY = marginYMM + (blockSizeMM / 2f)

        val jsonObject = JSONObject(jsonString)
        val childrenArray = jsonObject.getJSONArray("children")

        var minX = Float.MAX_VALUE
        var maxX = -Float.MAX_VALUE
        var minY = Float.MAX_VALUE
        var maxY = -Float.MAX_VALUE

        for (i in 0 until childrenArray.length()) {
            val node = childrenArray.getJSONObject(i)
            val nX = node.getDouble("x").toFloat()
            val nY = node.getDouble("y").toFloat()
            val nWidth = node.getDouble("width").toFloat()
            val nHeight = node.getDouble("height").toFloat()

            val centerX = nX + (nWidth / 2f)
            val centerY = -(nY + (nHeight / 2f))

            minX = min(minX, centerX)
            maxX = max(maxX, centerX)
            minY = min(minY, centerY)
            maxY = max(maxY, centerY)
        }

        val edgesArray = jsonObject.optJSONArray("edges")
        if (edgesArray != null) {
            for (i in 0 until edgesArray.length()) {
                val edge = edgesArray.getJSONObject(i)
                val sections = edge.optJSONArray("sections")
                if (sections != null) {
                    for (j in 0 until sections.length()) {
                        val section = sections.getJSONObject(j)
                        val bendPoints = section.optJSONArray("bendPoints")
                        if (bendPoints != null) {
                            for (k in 0 until bendPoints.length()) {
                                val bp = bendPoints.getJSONObject(k)
                                val bpX = bp.getDouble("x").toFloat()
                                val bpY = -bp.getDouble("y").toFloat()

                                minX = min(minX, bpX)
                                maxX = max(maxX, bpX)
                                minY = min(minY, bpY)
                                maxY = max(maxY, bpY)
                            }
                        }
                    }
                }
            }
        }

        val gridSpacing = min(
            (baseWidthMM - (safeMarginX * 2)) / max(1f, maxX - minX),
            (baseHeightMM - (safeMarginY * 2)) / max(1f, maxY - minY)
        )

        val xOffsetMM = (baseWidthMM / 2f) - (((minX + maxX) / 2f) * gridSpacing)
        val yOffsetMM = (baseHeightMM / 2f) - (((minY + maxY) / 2f) * gridSpacing)

        for (i in 0 until childrenArray.length()) {
            val node = childrenArray.getJSONObject(i)
            val nodeId = node.optString("id")
            val nX = node.getDouble("x").toFloat()
            val nY = node.getDouble("y").toFloat()
            val nWidth = node.getDouble("width").toFloat()
            val nHeight = node.getDouble("height").toFloat()

            val labelsArray = node.optJSONArray("labels")
            val baseText = if (labelsArray != null && labelsArray.length() > 0) {
                labelsArray.getJSONObject(0).getString("text")
            } else {
                "Node"
            }

            val shapeType = node.optString("myCustomShape", "square")

            val logicalMeaning = when(shapeType) {
                "circle" -> if (baseText.contains("START", ignoreCase = true)) "Nodo Inizio" else "Nodo Fine"
                "diamond" -> "Nodo Decisione"
                "trapezoid" -> "Nodo Input/Output"
                else -> "Nodo Processo"
            }

            val buttonText = "($logicalMeaning)\n$baseText "

            var spokenText = "$logicalMeaning. $baseText. "
            spokenText = spokenText.replace("<=", " minore di ")
                .replace(">=", " maggiore o uguale di ")
                .replace("==", " uguale a ")
                .replace("!=", " diverso da ")
                .replace("<", " minore di ")
                .replace(">", " maggiore di ")
                .replace("++", " più uno ")
                .replace("--", " meno uno ")
                .replace("+", " più ")
                .replace("-", " meno ")
                .replace("=", " uguale a ")

            var routingText = " "
            if (edgesArray != null) {
                for (j in 0 until edgesArray.length()) {
                    val edge = edgesArray.getJSONObject(j)
                    if (edge.optString("source") == nodeId) {

                        var edgeLabel = ""
                        val edgeLabels = edge.optJSONArray("labels")
                        if (edgeLabels != null && edgeLabels.length() > 0) {
                            edgeLabel = edgeLabels.getJSONObject(0).optString("text")
                        }

                        var direction = ""
                        val sections = edge.optJSONArray("sections")
                        if (sections != null && sections.length() > 0) {
                            val section = sections.getJSONObject(0)
                            val startPt = section.getJSONObject("startPoint")
                            val startX = startPt.getDouble("x")
                            val startY = startPt.getDouble("y")

                            var nextX = startX
                            var nextY = startY

                            val bendPoints = section.optJSONArray("bendPoints")
                            if (bendPoints != null && bendPoints.length() > 0) {
                                nextX = bendPoints.getJSONObject(0).getDouble("x")
                                nextY = bendPoints.getJSONObject(0).getDouble("y")
                            } else {
                                val endPt = section.getJSONObject("endPoint")
                                nextX = endPt.getDouble("x")
                                nextY = endPt.getDouble("y")
                            }

                            val dx = nextX - startX
                            val dy = nextY - startY

                            if (abs(dx) > abs(dy)) {
                                direction = if (dx > 0) " a destra " else "a sinistra "
                            } else {
                                direction = if (dy > 0) "giù " else "su "
                            }
                        }

                        routingText += if (edgeLabel.isNotEmpty()) {
                            " Arco $edgeLabel va $direction. "
                        } else {
                            " Arco va $direction. "
                        }
                    }
                }
            }

            if (routingText.trim().isNotEmpty()) {
                spokenText += "... " + routingText.trim()
            }

            val centerX = nX + (nWidth / 2f)
            val centerY = -(nY + (nHeight / 2f))

            val physicalX_MM = (centerX * gridSpacing) + xOffsetMM
            val rawPhysicalY_MM = (centerY * gridSpacing) + yOffsetMM

            val physicalY_MM = baseHeightMM - rawPhysicalY_MM

            val playMM = 2.0f
            val drawnSizeMM = blockSizeMM + playMM

            val pixelX = mmToPixelsX(physicalX_MM - (drawnSizeMM / 2f))
            val pixelY = mmToPixelsY(physicalY_MM - (drawnSizeMM / 2f))
            val pixelWidth = mmToPixelsX(drawnSizeMM)
            val pixelHeight = mmToPixelsY(drawnSizeMM)

            val button = Button(this@MainActivity)
            button.text = buttonText
            button.isAllCaps = false
            button.textSize = 10f

            button.setOnClickListener {
                println("Tapped: $buttonText. -> Spoken: $spokenText")
                tts.speak(spokenText, TextToSpeech.QUEUE_FLUSH, null, "")
            }

            val params = FrameLayout.LayoutParams(pixelWidth, pixelHeight)
            params.leftMargin = pixelX
            params.topMargin = pixelY

            button.layoutParams = params
            canvas.addView(button)
        }
    }

    override fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) {

            // 1. Tell the engine to use Italian (Italy)
            val result = tts.setLanguage(Locale.ITALY)

            // 2. Check if the tablet actually has the language installed!
            if (result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED) {
                println("TTS Error: The Italian language pack is missing or not supported on this tablet! Please download it in Android Settings.")
            } else {
                // 3. If successful, slow the voice down slightly so it's easier to understand
                tts.setSpeechRate(0.85f)
                tts.setPitch(0.9f)
            }

        } else {
            println("Text-To-Speech initialization failed.")
        }
    }

    override fun onDestroy() {
        if (::tts.isInitialized) {
            tts.stop()
            tts.shutdown()
        }
        super.onDestroy()
    }

    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        if (hasFocus) {
            hideSystemBars()
        }
    }

    private fun hideSystemBars() {
        androidx.core.view.WindowCompat.setDecorFitsSystemWindows(window, false)
        val windowInsetsController = androidx.core.view.WindowCompat.getInsetsController(window, window.decorView)
        windowInsetsController.hide(androidx.core.view.WindowInsetsCompat.Type.systemBars())
        windowInsetsController.systemBarsBehavior = androidx.core.view.WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
    }
}
