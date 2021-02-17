import org.joor.Reflect
import java.util.*
import java.util.function.Supplier


fun main(args: Array<String>) {

    val className = "mypackage.MyClass"
    val javaCode = """
    public int xvceller() {
        System.out.println("RUnninghere");
        return 2;
    }
"""
    val evaluatedMethod = evalMethod(javaCode, "xvceller","int", arrayOf())
    println(evaluatedMethod);
}

fun evalMethod(functionString: String, functionName: String, functionReturnType: String, functionArgs: Array<String>): Any {
    val java = """
       package wrappers;
        public class JavaWrappedClass {
         $functionString
        }
    """.trimIndent();

    Reflect.compile("wrappers.JavaWrappedClass", java).create();
    val classObj = Class.forName("wrappers.JavaWrappedClass")
    val classInst = classObj.newInstance();

    if (functionArgs.isEmpty()) { // No args to pass to function, don't pass anything
        return classObj.getMethod(functionName).invoke(classInst);
    }
    else {
        return classObj.getMethod(functionName).invoke(classInst, functionArgs);
    }
}